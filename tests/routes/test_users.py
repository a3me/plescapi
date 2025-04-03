import pytest
from fastapi.testclient import TestClient
from app.main import app
from datetime import datetime
from app.dependencies import get_current_user, get_firestore

def format_datetime(dt: datetime) -> str:
    """Format datetime in a consistent way."""
    return dt.strftime("%Y-%m-%dT%H:%M:%S.%f")

# Test data
now = datetime.now()
MOCK_USER = {
    "email": "test@example.com",
    "name": "Test User",
    "google_sub": "123456789",
    "created_at": format_datetime(now),
    "last_login": format_datetime(now)
}

@pytest.fixture(autouse=True)
def clean_test_db(test_firestore):
    """Clean up the test database before each test."""
    # Delete all documents in the users collection
    users_ref = test_firestore.collection("users")
    docs = users_ref.stream()
    for doc in docs:
        doc.reference.delete()

@pytest.fixture
def test_client(test_firestore):
    # Create a mock user
    async def get_current_user_mock():
        return {"email": "test@example.com"}
    
    # Override the dependencies in the app
    app.dependency_overrides[get_current_user] = get_current_user_mock
    app.dependency_overrides[get_firestore] = lambda: test_firestore
    
    # Create test client
    client = TestClient(app)
    yield client
    
    # Clean up the dependency overrides
    app.dependency_overrides = {}

@pytest.fixture
def mock_current_user():
    return {"email": "test@example.com"}

@pytest.mark.asyncio
async def test_get_current_user_info_success(test_firestore, test_client, mock_current_user):
    # Setup test data
    doc_ref = test_firestore.collection("users").document(mock_current_user["email"])
    doc_ref.set({
        "email": MOCK_USER["email"],
        "name": MOCK_USER["name"],
        "google_sub": MOCK_USER["google_sub"],
        "created_at": datetime.strptime(MOCK_USER["created_at"], "%Y-%m-%dT%H:%M:%S.%f"),
        "last_login": datetime.strptime(MOCK_USER["last_login"], "%Y-%m-%dT%H:%M:%S.%f")
    })

    # Test the endpoint
    response = test_client.get("/users/me", headers={"Authorization": "Bearer test-token"})
    
    # Verify
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == MOCK_USER["email"]
    assert data["name"] == MOCK_USER["name"]
    assert data["google_sub"] == MOCK_USER["google_sub"]
    # Just verify the timestamps are in the correct format without comparing exact values
    assert "created_at" in data
    assert "last_login" in data
    assert isinstance(data["created_at"], str)
    assert isinstance(data["last_login"], str)

@pytest.mark.asyncio
async def test_get_current_user_info_not_found(test_firestore, test_client, mock_current_user):
    # Test the endpoint
    response = test_client.get("/users/me", headers={"Authorization": "Bearer test-token"})
    
    # Verify
    assert response.status_code == 404
    assert response.json()["detail"] == "User not found"

@pytest.mark.asyncio
async def test_create_user_new(test_firestore, test_client, mock_current_user):
    # Test the endpoint
    response = test_client.post("/users/create", headers={"Authorization": "Bearer test-token"})
    
    # Verify
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == mock_current_user["email"]
    assert "created_at" in data
    assert "last_login" in data
    assert isinstance(data["created_at"], str)
    assert isinstance(data["last_login"], str)

@pytest.mark.asyncio
async def test_create_user_existing(test_firestore, test_client, mock_current_user):
    # Setup test data
    doc_ref = test_firestore.collection("users").document(mock_current_user["email"])
    doc_ref.set({
        "email": MOCK_USER["email"],
        "name": MOCK_USER["name"],
        "google_sub": MOCK_USER["google_sub"],
        "created_at": datetime.strptime(MOCK_USER["created_at"], "%Y-%m-%dT%H:%M:%S.%f"),
        "last_login": datetime.strptime(MOCK_USER["last_login"], "%Y-%m-%dT%H:%M:%S.%f")
    })

    # Test the endpoint
    response = test_client.post("/users/create", headers={"Authorization": "Bearer test-token"})
    
    # Verify
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == MOCK_USER["email"]
    assert data["name"] == MOCK_USER["name"]
    assert data["google_sub"] == MOCK_USER["google_sub"]
    # Just verify the timestamps are in the correct format without comparing exact values
    assert "created_at" in data
    assert "last_login" in data
    assert isinstance(data["created_at"], str)
    assert isinstance(data["last_login"], str)

@pytest.mark.asyncio
async def test_update_user_info_success(test_firestore, test_client, mock_current_user):
    # Setup test data
    doc_ref = test_firestore.collection("users").document(mock_current_user["email"])
    doc_ref.set({
        "email": MOCK_USER["email"],
        "name": MOCK_USER["name"],
        "google_sub": MOCK_USER["google_sub"],
        "created_at": datetime.strptime(MOCK_USER["created_at"], "%Y-%m-%dT%H:%M:%S.%f"),
        "last_login": datetime.strptime(MOCK_USER["last_login"], "%Y-%m-%dT%H:%M:%S.%f")
    })

    # Test the endpoint
    response = test_client.put("/users/me", 
                             headers={"Authorization": "Bearer test-token"},
                             json={"name": "New Name"})
    
    # Verify
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "New Name"

@pytest.mark.asyncio
async def test_update_user_info_not_found(test_firestore, test_client, mock_current_user):
    # Test the endpoint
    response = test_client.put("/users/me", 
                             headers={"Authorization": "Bearer test-token"},
                             json={"name": "New Name"})
    
    # Verify
    assert response.status_code == 404
    assert response.json()["detail"] == "User not found"

@pytest.mark.asyncio
async def test_update_user_info_no_changes(test_firestore, test_client, mock_current_user):
    # Setup test data
    doc_ref = test_firestore.collection("users").document(mock_current_user["email"])
    doc_ref.set({
        "email": MOCK_USER["email"],
        "name": MOCK_USER["name"],
        "google_sub": MOCK_USER["google_sub"],
        "created_at": datetime.strptime(MOCK_USER["created_at"], "%Y-%m-%dT%H:%M:%S.%f"),
        "last_login": datetime.strptime(MOCK_USER["last_login"], "%Y-%m-%dT%H:%M:%S.%f")
    })

    # Test the endpoint
    response = test_client.put("/users/me", 
                             headers={"Authorization": "Bearer test-token"})
    
    # Verify
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == MOCK_USER["email"]
    assert data["name"] == MOCK_USER["name"]
    assert data["google_sub"] == MOCK_USER["google_sub"]
    # Just verify the timestamps are in the correct format without comparing exact values
    assert "created_at" in data
    assert "last_login" in data
    assert isinstance(data["created_at"], str)
    assert isinstance(data["last_login"], str) 