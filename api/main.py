# main.py
import os
import asyncio
import datetime
import random
import uuid
import hashlib

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

from model.constants import SESSION_TTL_MINUTES
from model.emotion_classifier import detect_emotion
from model.behavior import apply_typing_modifier
from model.emotion_colors import EMOTION_THEMES
from api.prompt_engine import build_prompt
from api.groq_client import get_llm_response

# ── Time of Day Context ────────────────────────────────────────────────────
def get_time_context() -> str:
    hour = datetime.datetime.now().hour
    if 5 <= hour < 12:
        return "The person is starting their day. Be energetic and hopeful."
    elif 12 <= hour < 17:
        return "The person is in the middle of their day. Ground them."
    elif 17 <= hour < 21:
        return "The person is winding down. Help them reflect peacefully."
    else:
        return "Be extra gentle and warm. Bring calm and safety."

# ── Emotion Shift Detection ────────────────────────────────────────────────
def detect_emotional_shift(history: list) -> str:
    emotions = [
        m.get('emotion') for m in history
        if m.get('role') == 'user' and m.get('emotion')
    ]
    if len(emotions) < 2:
        return ""
    negative = {'sadness', 'anger', 'fear', 'grief', 'disappointment',
                 'remorse', 'nervousness', 'annoyance', 'disgust',
                 'confusion', 'embarrassment', 'disapproval'}
    positive = {'joy', 'excitement', 'gratitude', 'optimism', 'relief',
                 'pride', 'love', 'admiration', 'amusement', 'approval', 'caring'}
    first = emotions[0]
    last = emotions[-1]
    if first in negative and last in positive:
        return "The person has shifted to a more positive feeling. Acknowledge this gently."
    elif first in positive and last in negative:
        return "The person's mood has dropped. Be gentler than usual."
    elif first in negative and last in negative:
        return "The person has been struggling throughout. Be extra warm and present."
    return ""

# ── User Storage ───────────────────────────────────────────────────────────
users_db: dict = {}
sessions_db: dict = {}

# ── App Setup ──────────────────────────────────────────────────────────────
app = FastAPI(title='Soulify API', version='1.0.0')

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_methods=['*'],
    allow_headers=['*'],
)

conversation_history: dict[str, dict] = {}

# ── Models ─────────────────────────────────────────────────────────────────
class SignupRequest(BaseModel):
    name: str
    email: str
    password: str

class LoginRequest(BaseModel):
    email: str
    password: str

class AuthResponse(BaseModel):
    success: bool
    message: str
    user_id: str = ""
    session_id: str = ""
    name: str = ""

class ChatRequest(BaseModel):
    message: str
    session_id: str
    user_id: str
    typing_speed: float = 5.0
    user_name: str = ""

class ChatResponse(BaseModel):
    reply: str
    emotion: str
    confidence: float
    theme: dict
    quote: dict | None = None

# ── Auth Endpoints ─────────────────────────────────────────────────────────
@app.post('/signup', response_model=AuthResponse)
async def signup(req: SignupRequest):
    if req.email in users_db:
        return AuthResponse(success=False, message="Email already registered.")
    user_id = str(uuid.uuid4())
    password_hash = hashlib.sha256(req.password.encode()).hexdigest()
    users_db[req.email] = {
        "name": req.name,
        "email": req.email,
        "password_hash": password_hash,
        "user_id": user_id,
    }
    session_id = str(uuid.uuid4())
    sessions_db[session_id] = user_id
    return AuthResponse(
        success=True,
        message="Account created successfully.",
        user_id=user_id,
        session_id=session_id,
        name=req.name,
    )

@app.post('/login', response_model=AuthResponse)
async def login(req: LoginRequest):
    user = users_db.get(req.email)
    password_hash = hashlib.sha256(req.password.encode()).hexdigest()
    if not user or user["password_hash"] != password_hash:
        return AuthResponse(success=False, message="Invalid email or password.")
    session_id = str(uuid.uuid4())
    sessions_db[session_id] = user["user_id"]
    return AuthResponse(
        success=True,
        message="Logged in successfully.",
        user_id=user["user_id"],
        session_id=session_id,
        name=user["name"],
    )

@app.post('/logout')
async def logout(session_id: str):
    sessions_db.pop(session_id, None)
    return {"success": True, "message": "Logged out."}

# ── General Endpoints ──────────────────────────────────────────────────────
@app.get('/')
def root():
    return {'status': 'Soulify API is running'}

@app.post('/chat', response_model=ChatResponse)
async def chat(req: ChatRequest):
    now = datetime.datetime.utcnow().timestamp()

    session_data = conversation_history.get(
        req.session_id, {'history': [], 'last_seen': now}
    )
    history = session_data.get('history', [])

    emotion_result = await asyncio.to_thread(detect_emotion, req.message, req.session_id)
    emotion = emotion_result['emotion']
    confidence = apply_typing_modifier(emotion, emotion_result['confidence'], req.typing_speed)

    time_context = get_time_context()
    shift_context = detect_emotional_shift(history)

    extra = f"\nTime of day context: {time_context}\n"
    if shift_context:
        extra += f"\nEmotional journey note: {shift_context}\n"

    messages = build_prompt(
        req.message, emotion, confidence, history,
        extra_instruction=extra,
        user_name=req.user_name
    )
    llm_reply = await get_llm_response(messages)

    history.append({'role': 'user', 'content': req.message, 'emotion': emotion})
    history.append({'role': 'assistant', 'content': llm_reply, 'had_quote': False})
    conversation_history[req.session_id] = {'history': history[-10:], 'last_seen': now}

    theme = EMOTION_THEMES.get(emotion, EMOTION_THEMES['neutral'])
    return ChatResponse(
        reply=llm_reply,
        emotion=emotion,
        confidence=round(confidence, 3),
        theme=theme,
        quote=None,
    )

@app.get('/health')
async def health():
    return {'status': 'healthy', 'timestamp': datetime.datetime.utcnow().isoformat()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)