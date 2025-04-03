# Pleść API

A FastAPI-based backend for the Pleść Polish language learning application.

## Requirements

- Python 3.13.2
- Docker and Docker Compose
- Java 17 (for Firebase emulators)
- Firebase CLI (for local development)

## Installation

### Local Development

1. Create and activate a virtual environment:
```bash
python3 -m venv env
source env/bin/activate  # On Windows: env\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up Firebase emulators:
```bash
# Install Firebase CLI if not already installed
curl -sL https://firebase.tools | bash

# Initialize Firebase emulators
firebase init emulators --project demo-test
```

4. Create a `.env` file in the root directory with the following variables:
```env
GOOGLE_CLIENT_ID=your_client_id
GOOGLE_CLIENT_SECRET=your_client_secret
GEMINI_API_KEY=your_gemini_key
SECRET_KEY=your_secret_key
ALGORITHM=HS256
GOOGLE_APPLICATION_CREDENTIALS=/app/plesc-455015-5e588ea78c9c.json
```

### Docker Deployment

1. Build and run using Docker Compose:
```bash
docker compose up --build
```

2. For development with hot-reload:
```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build
```

The API will be available at `http://localhost:8000`

## Development

### Running the API Locally

1. Start the Firestore emulator:
```bash
firebase emulators:start --only firestore
```

2. In a new terminal, start the API:
```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

### API Documentation

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Testing

### Local Testing

1. Start the Firestore emulator:
```bash
firebase emulators:start --only firestore
```

2. In a new terminal, run the tests:
```bash
pytest tests/ -v
```

### Test Environment Variables

The following environment variables are used in tests:
```env
GOOGLE_CLIENT_ID=test-client-id
GOOGLE_CLIENT_SECRET=test-client-secret
GEMINI_API_KEY=test-gemini-key
GOOGLE_PROJECT_ID=test-project-id
FIRESTORE_EMULATOR_HOST=localhost:8080
SECRET_KEY=test-secret-key
ALGORITHM=HS256
```

### CI/CD Testing

Tests are automatically run on GitHub Actions for:
- Push to main branch
- Pull requests to main branch

## Dependencies

To update the requirements file:
```bash
pip freeze > requirements.txt
```