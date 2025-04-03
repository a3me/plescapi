import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import pytest
from google.cloud import firestore

# Add the project root directory to the Python path
project_root = str(Path(__file__).parent.parent)
sys.path.insert(0, project_root)

# Set test environment variables before any imports
os.environ['GOOGLE_CLIENT_ID'] = 'test-client-id'
os.environ['GOOGLE_CLIENT_SECRET'] = 'test-client-secret'
os.environ['GEMINI_API_KEY'] = 'test-gemini-key'
os.environ['GOOGLE_PROJECT_ID'] = 'test-project-id'
os.environ['FIRESTORE_EMULATOR_HOST'] = 'localhost:8080'
os.environ['SECRET_KEY'] = 'test-secret-key'
os.environ['ALGORITHM'] = 'HS256'

# Load test environment variables from .env.test file
test_env_path = Path(__file__).parent / '.env.test'
load_dotenv(test_env_path)

@pytest.fixture(autouse=True)
def test_firestore():
    # Initialize Firestore client with emulator
    client = firestore.Client(project='test-project-id')
    yield client
    # Clean up after tests
    for collection in client.collections():
        for doc in collection.stream():
            doc.reference.delete() 