from fastapi import FastAPI
from app.auth import router as auth_router
# from app.routes import lessons, roleplay, pronunciation, explore, users

app = FastAPI(title="Pleść API")

app.include_router(auth_router, prefix="/auth")
# app.include_router(lessons.router, prefix="/lessons")
# app.include_router(roleplay.router, prefix="/roleplay")
# app.include_router(pronunciation.router, prefix="/pronunciation")
# app.include_router(explore.router, prefix="/explore")
# app.include_router(users.router, prefix="/users")

@app.get("/")
async def root():
    return {"message": "Welcome to Pleść API"}


@app.get("/health")
async def health():
    return {"status": "ok"}
