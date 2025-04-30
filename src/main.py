from fastapi import FastAPI, HTTPException, status
from src.routes import collection, dashboard, media, settings, auth, user, ai, search
from pydantic import BaseModel
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from src.utils.db import init_mongodb
from src.ai.gemini import run_gemini_chat
from src.ai.pyd_ai import run_gemini_chat as gemini_chat
from src.models.user import User
from src.models.user_settings import UserSettings
from src.models.token import BlacklistedToken


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Server running on port 8000")
    # Initialize MongoDB connection
    db = await init_mongodb("ai-multimedia")
    yield
    print("Server stopped")


app = FastAPI(lifespan=lifespan)

# Allow connections from the frontend development server
origins = ["https://ai-multimedia-frontend.onrender.com/"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/")
async def root() -> dict[str, str]:
    try:
        print("No Error encountered")
        return {"message": "Hello, world"}
    except Exception as e:
        print("Error encountered")
        print(str(e))


class Message(BaseModel):
    msg: str


class ChatMessage(BaseModel):
    role: str
    text: str


class ChatRequest(BaseModel):
    messages: list[ChatMessage]


@app.post("/api/")
def send_message(message: Message):
    try:
        response = run_gemini_chat(message.msg)
        return {"response": response}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"Error": "Error generating message"},
        )


@app.post("/api/chat")
def chat(request: ChatRequest):
    try:
        # Convert from the request format to the format expected by gemini_chat
        chat_messages = [
            {"role": msg.role, "text": msg.text} for msg in request.messages
        ]

        response = gemini_chat(chat_messages)
        return {"response": response}
    except Exception as e:
        print(f"Chat error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"Error": "Error generating chat response"},
        )


# Include all routers with API prefix
app.include_router(auth.router, prefix="/api")
app.include_router(user.router, prefix="/api")
app.include_router(dashboard.router, prefix="/api")
app.include_router(collection.router, prefix="/api")
app.include_router(media.router, prefix="/api")
app.include_router(settings.router, prefix="/api")
app.include_router(ai.router, prefix="/api")
app.include_router(search.router, prefix="/api")
