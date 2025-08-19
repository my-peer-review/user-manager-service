import pytest
from uuid import uuid4

from app.services.user_service import UserService, _hash_password
from app.schemas.user import UserCreate, UserLogin, User

# ------------------------- Fake repository (minimale) -------------------------
class FakeUserRepo:
    def __init__(self):
        # key: email, value: (User, hashed_password)
        self._by_email: dict[str, tuple[User, str]] = {}
        self._created_ids: list[str] = []

    async def get_by_email(self, email: str):
        rec = self._by_email.get(email)
        if not rec:
            return None
        user, _ = rec
        return user

    async def create(self, data: UserCreate, *, hashed_password: str) -> int:
        # Simula vincolo UNIQUE su email
        if data.email and data.email in self._by_email:
            raise Exception("UNIQUE VIOLATION: email already used")
        new_id = str(uuid4())
        user = User(userId=new_id, username=data.username, email=data.email, role=data.role)
        if data.email:
            self._by_email[data.email] = (user, hashed_password)
        self._created_ids.append(str(new_id))
        return new_id

    async def get_auth_by_email(self, email: str):
        # Ritorna la tupla (User, hashed_password) oppure None
        return self._by_email.get(email)


# --------------------------------- Fixtures ----------------------------------
@pytest.fixture
def repo():
    return FakeUserRepo()


# ---------------------------------- Tests ------------------------------------
@pytest.mark.asyncio
async def test_register_ok(repo):
    data = UserCreate(username="  Alice  ", password="s3cr3t", email="ALICE@EXAMPLE.COM", role="student")
    new_id = await UserService.register(data, repo)

    assert new_id
    # è stato normalizzato: username strip, email lower
    user = await repo.get_by_email("alice@example.com")
    assert user is not None
    assert user.username == "Alice"
    assert user.email == "alice@example.com"

@pytest.mark.asyncio
async def test_register_email_già_esistente_precheck(repo):
    # seed utente esistente
    u1 = UserCreate(username="Bob", password="x", email="bob@example.com", role="student")
    await UserService.register(u1, repo)

    # tentativo con la stessa email -> ValueError("Email already exists")
    with pytest.raises(ValueError) as exc:
        await UserService.register(UserCreate(username="Another", password="x", email="bob@example.com", role="student"), repo)
    assert "Email already exists" in str(exc.value)


@pytest.mark.asyncio
async def test_register_race_condition_repo_lancia_unique(repo, monkeypatch):
    # forziamo repo.create a lanciare un'eccezione (es. vincolo UNIQUE a DB)
    async def boom(data, *, hashed_password):
        raise Exception("duplicate key value violates unique constraint")

    monkeypatch.setattr(repo, "create", boom, raising=True)

    with pytest.raises(ValueError) as exc:
        await UserService.register(UserCreate(username="X", password="p", email="x@example.com", role="student"), repo)
    assert "User already exists" in str(exc.value)


@pytest.mark.asyncio
async def test_authenticate_ok(repo):
    # seed
    email = "carol@example.com"
    user = User(userId="ABXF", username="carol", email=email, role="student")
    hashed = _hash_password("pw")
    repo._by_email[email] = (user, hashed)

    # login via email
    found = await UserService.authenticate(UserLogin(email=email, password="pw"), repo)
    assert found is not None
    assert found.username == "carol"


@pytest.mark.asyncio
async def test_authenticate_password_errato(repo):
    email = "dave@example.com"
    user = User(userId="ABXFDFG", username="dave", email=email, role="student")
    hashed = _hash_password("right")
    repo._by_email[email] = (user, hashed)

    found = await UserService.authenticate(UserLogin(email=email, password="WRONG"), repo)
    assert found is None


@pytest.mark.asyncio
async def test_authenticate_email_non_trovata(repo):
    found = await UserService.authenticate(UserLogin(email="missing@example.com", password="pw"), repo)
    assert found is None