import pytest
from fastapi.testclient import TestClient
from app.main import app
from datetime import datetime
from app.dependencies import get_current_user, get_firestore

# Test data
MOCK_BOT = {
    "id": "test-bot-id",
    "name": "Test Bot",
    "description": "A test bot for testing",
    "prompt": "You are a test bot",
    "image_url": "https://example.com/image.jpg",
    "created_by": "test@example.com",
    "created_at": datetime.now()
}

def format_datetime(dt: datetime) -> str:
    """Format datetime in a consistent way."""
    return dt.strftime("%Y-%m-%dT%H:%M:%S.%f")

@pytest.fixture(autouse=True)
def clean_test_db(test_firestore):
    """Clean up the test database before each test."""
    # Delete all documents in the bots collection
    bots_ref = test_firestore.collection("bots")
    docs = bots_ref.stream()
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
async def test_create_bot_success(test_firestore, test_client, mock_current_user):
    # Test the endpoint
    response = test_client.post(
        "/bots",
        headers={"Authorization": "Bearer test-token"},
        json={
            "name": MOCK_BOT["name"],
            "description": MOCK_BOT["description"],
            "prompt": MOCK_BOT["prompt"],
            "image_url": MOCK_BOT["image_url"]
        }
    )
    
    # Verify
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == MOCK_BOT["name"]
    assert data["description"] == MOCK_BOT["description"]
    assert data["prompt"] == MOCK_BOT["prompt"]
    assert data["image_url"] == MOCK_BOT["image_url"]
    assert data["created_by"] == mock_current_user["email"]
    assert "id" in data
    assert "created_at" in data
    assert isinstance(data["created_at"], str)
    # Verify the datetime format
    datetime.strptime(data["created_at"], "%Y-%m-%dT%H:%M:%S.%f")

@pytest.mark.asyncio
async def test_get_bots_success(test_firestore, test_client, mock_current_user):
    # Setup test data
    doc_ref = test_firestore.collection("bots").document(MOCK_BOT["id"])
    doc_ref.set({
        "id": MOCK_BOT["id"],
        "name": MOCK_BOT["name"],
        "description": MOCK_BOT["description"],
        "prompt": MOCK_BOT["prompt"],
        "image_url": MOCK_BOT["image_url"],
        "created_by": mock_current_user["email"],
        "created_at": MOCK_BOT["created_at"]
    })

    # Test the endpoint
    response = test_client.get("/bots", headers={"Authorization": "Bearer test-token"})
    
    # Verify
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == MOCK_BOT["id"]
    assert data[0]["name"] == MOCK_BOT["name"]
    assert data[0]["description"] == MOCK_BOT["description"]
    assert data[0]["prompt"] == MOCK_BOT["prompt"]
    assert data[0]["image_url"] == MOCK_BOT["image_url"]
    assert data[0]["created_by"] == mock_current_user["email"]

@pytest.mark.asyncio
async def test_get_bot_success(test_firestore, test_client, mock_current_user):
    # Setup test data
    doc_ref = test_firestore.collection("bots").document(MOCK_BOT["id"])
    doc_ref.set({
        "id": MOCK_BOT["id"],
        "name": MOCK_BOT["name"],
        "description": MOCK_BOT["description"],
        "prompt": MOCK_BOT["prompt"],
        "image_url": MOCK_BOT["image_url"],
        "created_by": mock_current_user["email"],
        "created_at": MOCK_BOT["created_at"]
    })

    # Test the endpoint
    response = test_client.get(f"/bots/{MOCK_BOT['id']}", headers={"Authorization": "Bearer test-token"})
    
    # Verify
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == MOCK_BOT["id"]
    assert data["name"] == MOCK_BOT["name"]
    assert data["description"] == MOCK_BOT["description"]
    assert data["prompt"] == MOCK_BOT["prompt"]
    assert data["image_url"] == MOCK_BOT["image_url"]
    assert data["created_by"] == mock_current_user["email"]

@pytest.mark.asyncio
async def test_get_bot_not_found(test_firestore, test_client, mock_current_user):
    # Test the endpoint
    response = test_client.get(f"/bots/{MOCK_BOT['id']}", headers={"Authorization": "Bearer test-token"})
    
    # Verify
    assert response.status_code == 404
    assert response.json()["detail"] == "Bot not found"

@pytest.mark.asyncio
async def test_update_bot_success(test_firestore, test_client, mock_current_user):
    # Setup test data
    doc_ref = test_firestore.collection("bots").document(MOCK_BOT["id"])
    doc_ref.set({
        "id": MOCK_BOT["id"],
        "name": MOCK_BOT["name"],
        "description": MOCK_BOT["description"],
        "prompt": MOCK_BOT["prompt"],
        "image_url": MOCK_BOT["image_url"],
        "created_by": mock_current_user["email"],
        "created_at": MOCK_BOT["created_at"]
    })

    # Test the endpoint
    response = test_client.put(
        f"/bots/{MOCK_BOT['id']}",
        headers={"Authorization": "Bearer test-token"},
        json={"name": "Updated Bot Name", "description": "Updated description"}
    )
    
    # Verify
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == MOCK_BOT["id"]
    assert data["name"] == "Updated Bot Name"
    assert data["description"] == "Updated description"
    assert data["prompt"] == MOCK_BOT["prompt"]
    assert data["image_url"] == MOCK_BOT["image_url"]
    assert data["created_by"] == mock_current_user["email"]

@pytest.mark.asyncio
async def test_update_bot_not_found(test_firestore, test_client, mock_current_user):
    # Test the endpoint
    response = test_client.put(
        f"/bots/{MOCK_BOT['id']}",
        headers={"Authorization": "Bearer test-token"},
        json={"name": "Updated Bot Name"}
    )
    
    # Verify
    assert response.status_code == 404
    assert response.json()["detail"] == "Bot not found"

@pytest.mark.asyncio
async def test_update_bot_unauthorized(test_firestore, test_client, mock_current_user):
    # Setup test data with different creator
    doc_ref = test_firestore.collection("bots").document(MOCK_BOT["id"])
    doc_ref.set({
        "id": MOCK_BOT["id"],
        "name": MOCK_BOT["name"],
        "description": MOCK_BOT["description"],
        "prompt": MOCK_BOT["prompt"],
        "image_url": MOCK_BOT["image_url"],
        "created_by": "other@example.com",
        "created_at": MOCK_BOT["created_at"]
    })

    # Test the endpoint
    response = test_client.put(
        f"/bots/{MOCK_BOT['id']}",
        headers={"Authorization": "Bearer test-token"},
        json={"name": "Updated Bot Name"}
    )
    
    # Verify
    assert response.status_code == 403
    assert response.json()["detail"] == "Not authorized to update this bot"

@pytest.mark.asyncio
async def test_delete_bot_success(test_firestore, test_client, mock_current_user):
    # Setup test data
    doc_ref = test_firestore.collection("bots").document(MOCK_BOT["id"])
    doc_ref.set({
        "id": MOCK_BOT["id"],
        "name": MOCK_BOT["name"],
        "description": MOCK_BOT["description"],
        "prompt": MOCK_BOT["prompt"],
        "image_url": MOCK_BOT["image_url"],
        "created_by": mock_current_user["email"],
        "created_at": MOCK_BOT["created_at"]
    })

    # Test the endpoint
    response = test_client.delete(f"/bots/{MOCK_BOT['id']}", headers={"Authorization": "Bearer test-token"})
    
    # Verify
    assert response.status_code == 200
    assert response.json()["message"] == "Bot deleted successfully"
    
    # Verify bot is actually deleted
    bot_ref = test_firestore.collection("bots").document(MOCK_BOT["id"]).get()
    assert not bot_ref.exists

@pytest.mark.asyncio
async def test_delete_bot_not_found(test_firestore, test_client, mock_current_user):
    # Test the endpoint
    response = test_client.delete(f"/bots/{MOCK_BOT['id']}", headers={"Authorization": "Bearer test-token"})
    
    # Verify
    assert response.status_code == 404
    assert response.json()["detail"] == "Bot not found"

@pytest.mark.asyncio
async def test_delete_bot_unauthorized(test_firestore, test_client, mock_current_user):
    # Setup test data with different creator
    doc_ref = test_firestore.collection("bots").document(MOCK_BOT["id"])
    doc_ref.set({
        "id": MOCK_BOT["id"],
        "name": MOCK_BOT["name"],
        "description": MOCK_BOT["description"],
        "prompt": MOCK_BOT["prompt"],
        "image_url": MOCK_BOT["image_url"],
        "created_by": "other@example.com",
        "created_at": MOCK_BOT["created_at"]
    })

    # Test the endpoint
    response = test_client.delete(f"/bots/{MOCK_BOT['id']}", headers={"Authorization": "Bearer test-token"})
    
    # Verify
    assert response.status_code == 403
    assert response.json()["detail"] == "Not authorized to delete this bot" 