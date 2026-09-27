import uuid
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.core.security import get_current_user
from app.models.user import User


def create_test_env(app, email: str = "test@finpilot.ai"):
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    db = TestingSessionLocal()
    test_user = User(
        id=uuid.uuid4(),
        email=email,
        full_name="Test User",
        is_active=True,
    )
    db.add(test_user)
    db.commit()
    db.refresh(test_user)
    test_user_id = test_user.id
    db.close()

    def override_get_current_user():
        db = TestingSessionLocal()
        u = db.query(User).filter(User.id == test_user_id).first()
        db.close()
        return u

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user
    client = TestClient(app)

    return engine, TestingSessionLocal, test_user, client
