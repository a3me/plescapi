import pytest
from fastapi.testclient import TestClient
from app.main import app
from datetime import datetime
from app.dependencies import get_current_user, get_firestore
from uuid import uuid4
from unittest.mock import patch, MagicMock

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

MOCK_CHAT = {
    "id": "test-chat-id",
    "user_id": "test@example.com",
    "bot_id": "test-bot-id",
    "bot_prompt": "You are a test bot",
    "messages": []
}

@pytest.fixture(autouse=True)
def clean_test_db(test_firestore):
    """Clean up the test database before each test."""
    # Delete all documents in the chats and bots collections
    chats_ref = test_firestore.collection("chats")
    bots_ref = test_firestore.collection("bots")
    
    for doc in chats_ref.stream():
        doc.reference.delete()
    for doc in bots_ref.stream():
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

@pytest.fixture
def setup_bot(test_firestore):
    """Setup a test bot in Firestore."""
    bot_ref = test_firestore.collection("bots").document(MOCK_BOT["id"])
    bot_ref.set(MOCK_BOT)
    return MOCK_BOT["id"]

@pytest.fixture
def mock_gemini_response():
    """Mock Gemini API response."""
    mock_response = MagicMock()
    mock_response.text = "This is a test response from the bot."
    return mock_response

@pytest.mark.asyncio
async def test_start_chat_success(test_firestore, test_client, mock_current_user, setup_bot):
    # Test the endpoint
    response = test_client.get(
        f"/chat/start?bot_id={setup_bot}",
        headers={"Authorization": "Bearer test-token"}
    )
    
    # Verify
    assert response.status_code == 200
    data = response.json()
    assert "chat_id" in data
    assert isinstance(data["chat_id"], str)
    
    # Verify chat was created in Firestore
    chat_ref = test_firestore.collection("chats").document(data["chat_id"]).get()
    assert chat_ref.exists
    chat_data = chat_ref.to_dict()
    assert chat_data["user_id"] == mock_current_user["email"]
    assert chat_data["bot_id"] == setup_bot
    assert chat_data["bot_prompt"] == MOCK_BOT["prompt"]
    assert chat_data["messages"] == []

@pytest.mark.asyncio
async def test_start_chat_bot_not_found(test_firestore, test_client, mock_current_user):
    # Test the endpoint with non-existent bot
    response = test_client.get(
        "/chat/start?bot_id=non-existent-bot",
        headers={"Authorization": "Bearer test-token"}
    )
    
    # Verify
    assert response.status_code == 404
    assert response.json()["detail"] == "Bot not found"

@pytest.mark.asyncio
async def test_get_chats_success(test_firestore, test_client, mock_current_user, setup_bot):
    # Setup test data
    chat_id = str(uuid4())
    chat_ref = test_firestore.collection("chats").document(chat_id)
    chat_ref.set({
        "user_id": mock_current_user["email"],
        "bot_id": setup_bot,
        "bot_prompt": MOCK_BOT["prompt"],
        "messages": []
    })

    # Test the endpoint
    response = test_client.get("/chat", headers={"Authorization": "Bearer test-token"})
    
    # Verify
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == chat_id
    assert data[0]["user_id"] == mock_current_user["email"]
    assert data[0]["bot_id"] == setup_bot
    assert data[0]["bot_prompt"] == MOCK_BOT["prompt"]
    assert data[0]["messages"] == []
    
    # Verify bot information is included
    assert "bot" in data[0]
    assert data[0]["bot"]["id"] == MOCK_BOT["id"]
    assert data[0]["bot"]["name"] == MOCK_BOT["name"]
    assert data[0]["bot"]["description"] == MOCK_BOT["description"]
    assert data[0]["bot"]["prompt"] == MOCK_BOT["prompt"]
    assert data[0]["bot"]["image_url"] == MOCK_BOT["image_url"]
    assert data[0]["bot"]["created_by"] == mock_current_user["email"]

@pytest.mark.asyncio
async def test_get_chat_success(test_firestore, test_client, mock_current_user, setup_bot):
    # Setup test data
    chat_id = str(uuid4())
    chat_ref = test_firestore.collection("chats").document(chat_id)
    chat_ref.set({
        "user_id": mock_current_user["email"],
        "bot_id": setup_bot,
        "bot_prompt": MOCK_BOT["prompt"],
        "messages": []
    })

    # Test the endpoint
    response = test_client.get(f"/chat/{chat_id}", headers={"Authorization": "Bearer test-token"})
    
    # Verify
    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == mock_current_user["email"]
    assert data["bot_id"] == setup_bot
    assert data["bot_prompt"] == MOCK_BOT["prompt"]
    assert data["messages"] == []

@pytest.mark.asyncio
async def test_get_chat_not_found(test_firestore, test_client, mock_current_user):
    # Test the endpoint
    response = test_client.get(
        "/chat/non-existent-chat",
        headers={"Authorization": "Bearer test-token"}
    )
    
    # Verify
    assert response.status_code == 404
    assert response.json()["detail"] == "Chat not found"

@pytest.mark.asyncio
async def test_get_chat_unauthorized(test_firestore, test_client, mock_current_user, setup_bot):
    # Setup test data with different user
    chat_id = str(uuid4())
    chat_ref = test_firestore.collection("chats").document(chat_id)
    chat_ref.set({
        "user_id": "other@example.com",
        "bot_id": setup_bot,
        "bot_prompt": MOCK_BOT["prompt"],
        "messages": []
    })

    # Test the endpoint
    response = test_client.get(f"/chat/{chat_id}", headers={"Authorization": "Bearer test-token"})
    
    # Verify
    assert response.status_code == 403
    assert response.json()["detail"] == "Not authorized to access this chat"

@pytest.mark.asyncio
async def test_send_message_success(test_firestore, test_client, mock_current_user, setup_bot, mock_gemini_response):
    # Setup test data
    chat_id = str(uuid4())
    chat_ref = test_firestore.collection("chats").document(chat_id)
    chat_ref.set({
        "user_id": mock_current_user["email"],
        "bot_id": setup_bot,
        "bot_prompt": MOCK_BOT["prompt"],
        "messages": []
    })

    # Mock the Gemini API client
    with patch('app.routes.chat.client.models.generate_content', return_value=mock_gemini_response):
        # Test the endpoint
        response = test_client.post(
            f"/chat/{chat_id}/message",
            headers={"Authorization": "Bearer test-token"},
            json={"message": "Hello, bot!"}
        )
        
        # Verify
        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        assert data["response"] == mock_gemini_response.text
        
        # Verify message was added to chat history
        chat_data = chat_ref.get().to_dict()
        assert len(chat_data["messages"]) == 2  # User message and bot response
        
        # Verify user message
        assert chat_data["messages"][0]["role"] == "user"
        assert chat_data["messages"][0]["content"] == "Hello, bot!"
        assert "timestamp" in chat_data["messages"][0]
        assert isinstance(chat_data["messages"][0]["timestamp"], datetime)
        
        # Verify bot response
        assert chat_data["messages"][1]["role"] == "assistant"
        assert chat_data["messages"][1]["content"] == mock_gemini_response.text
        assert "timestamp" in chat_data["messages"][1]
        assert isinstance(chat_data["messages"][1]["timestamp"], datetime)
        
        # Verify timestamps are present and in order
        assert chat_data["messages"][0]["timestamp"] <= chat_data["messages"][1]["timestamp"]

@pytest.mark.asyncio
async def test_send_message_chat_not_found(test_firestore, test_client, mock_current_user):
    # Test the endpoint
    response = test_client.post(
        "/chat/non-existent-chat/message",
        headers={"Authorization": "Bearer test-token"},
        json={"message": "Hello, bot!"}
    )
    
    # Verify
    assert response.status_code == 404
    assert response.json()["detail"] == "Chat not found"

@pytest.mark.asyncio
async def test_send_message_unauthorized(test_firestore, test_client, mock_current_user, setup_bot):
    # Setup test data with different user
    chat_id = str(uuid4())
    chat_ref = test_firestore.collection("chats").document(chat_id)
    chat_ref.set({
        "user_id": "other@example.com",
        "bot_id": setup_bot,
        "bot_prompt": MOCK_BOT["prompt"],
        "messages": []
    })

    # Test the endpoint
    response = test_client.post(
        f"/chat/{chat_id}/message",
        headers={"Authorization": "Bearer test-token"},
        json={"message": "Hello, bot!"}
    )
    
    # Verify
    assert response.status_code == 403
    assert response.json()["detail"] == "Not authorized to access this chat"

@pytest.mark.asyncio
async def test_delete_chat_success(test_firestore, test_client, mock_current_user, setup_bot):
    # Setup test data
    chat_id = str(uuid4())
    chat_ref = test_firestore.collection("chats").document(chat_id)
    chat_ref.set({
        "user_id": mock_current_user["email"],
        "bot_id": setup_bot,
        "bot_prompt": MOCK_BOT["prompt"],
        "messages": []
    })

    # Test the endpoint
    response = test_client.delete(f"/chat/{chat_id}", headers={"Authorization": "Bearer test-token"})
    
    # Verify
    assert response.status_code == 200
    assert response.json()["message"] == "Chat deleted"
    
    # Verify chat was deleted from Firestore
    assert not chat_ref.get().exists 