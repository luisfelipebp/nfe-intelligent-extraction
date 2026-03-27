import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import Base, get_db
from main import app
from sqlalchemy.pool import StaticPool


DATABASE_TEST_URL = "sqlite:///:memory:"

engine_test = create_engine(
    DATABASE_TEST_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)

SessionTest = sessionmaker(autocommit = False, autoflush=False, bind=engine_test)


@pytest.fixture(scope="function")
def db():
    Base.metadata.create_all(bind=engine_test)
    session = SessionTest()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine_test)


@pytest.fixture(scope="function")
def client(db):
    def override_get_db():
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    yield TestClient(app)

    app.dependency_overrides.clear()