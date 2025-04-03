from fastapi import FastAPI, Request, HTTPException
from app.auth import router as auth_router
from app.routes.chat import router as chat_router
from app.routes.users import router as users_router
import time
from app.config import settings

app = FastAPI(title="Pleść API")
app.include_router(auth_router, prefix="/auth")
app.include_router(chat_router, prefix="/chat")
app.include_router(users_router, prefix="/users")

@app.get("/")
async def root():
    return {"message": "Welcome to Pleść API"}

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.perf_counter()
    response = await call_next(request)
    process_time = time.perf_counter() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response