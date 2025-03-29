from fastapi import FastAPI
from app.auth import router as auth_router
from app.routes.chat import router as chat_router

app = FastAPI(title="Pleść API")

app.include_router(auth_router, prefix="/auth")
app.include_router(chat_router, prefix="/chat")

@app.get("/")
async def root():
    return {"message": "Welcome to Pleść API"}


@app.get("/health")
async def health():
    return {"status": "ok"}
