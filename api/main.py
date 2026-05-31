import os
import asyncio
import datetime

from fastapi import FastAPI # type: ignore
from fastapi.middleware.cors import CORSMiddleware # type: ignore
from pydantic import BaseModel # type: ignore
from dotenv import load_dotenv # type: ignore

load_dotenv()

import sys
# Ensure the project root is in sys.path for internal imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from model.emotion_classifier import detect_emotion
from model.behavior import apply_typing_modifier
from model.emotion_colors import EMOTION_THEMES
from api.prompt_engine import build_prompt
from api.groq_client import get_llm_response, generate_quote
from api.quote_manager import should_send_quote, get_seen_quotes, save_quote

app = FastAPI(title='Soulify API', version='1.0.0')

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_methods=['*'],
    allow_headers=['*'],
)

# In-memory conversation history: { session_id: {'history': list, 'last_seen': float} }
conversation_history: dict[str, dict] = {}


class ChatRequest(BaseModel):
    message: str
    session_id: str
    user_id: str
    typing_speed: float = 5.0


class ChatResponse(BaseModel):
    reply: str
    emotion: str
    confidence: float
    theme: dict
    quote: dict | None = None


@app.get('/')
def root():
    return {'status': 'Soulify API is running'}


@app.post('/chat', response_model=ChatResponse)
async def chat(req: ChatRequest):
    now = datetime.datetime.utcnow().timestamp()

    # ── Memory Management: Periodic Cleanup ────────────────────────────
    import random
    if random.random() < 0.05:  # Run cleanup on ~5% of requests to save CPU
        from model.constants import SESSION_TTL_MINUTES
        ttl_sec = SESSION_TTL_MINUTES * 60
        for sid in list(conversation_history.keys()):
            item = conversation_history[sid]
            if not isinstance(item, dict) or 'last_seen' not in item or (now - item['last_seen'] > ttl_sec):
                del conversation_history[sid]

    # Get history and last_seen
    session_data = conversation_history.get(req.session_id, {'history': [], 'last_seen': now})
    history = session_data.get('history', [])

    # ── Step 1: Run emotion detection ─────────────────────────────────────
    emotion_result = await asyncio.to_thread(
        detect_emotion, req.message, req.session_id
    )

    emotion = emotion_result['emotion']
    confidence = apply_typing_modifier(
        emotion, emotion_result['confidence'], req.typing_speed
    )

    # ── Step 2: Build emotion-aware prompt then fire LLM ───────────────────
    messages = build_prompt(req.message, emotion, confidence, history)
    llm_reply = await get_llm_response(messages)

    # ── Step 3: Quote trigger (optional, async + LLM) ──────────────────
    quote_data = None
    if should_send_quote(emotion, confidence, history):
        seen = await get_seen_quotes(req.user_id, emotion)
        quote_data = await generate_quote(emotion, req.message, seen)
        await save_quote(req.user_id, emotion, quote_data)
        # Combine the quote with the main response so it is returned as a single unified text string
        llm_reply += f'\n\n"{quote_data["quote"]}" — {quote_data["author"]} (Try this: {quote_data["exercise"]})'

    # ── Step 4: Update history (cap at last 10 turns) ─────────────────────
    history.append({'role': 'user', 'content': req.message, 'emotion': emotion})
    history.append({
        'role': 'assistant',
        'content': llm_reply,
        'had_quote': quote_data is not None,
    })

    conversation_history[req.session_id] = {
        'history': history[-10:],
        'last_seen': now
    }

    # ── Step 5: Return response ────────────────────────────────────────────
    theme = EMOTION_THEMES.get(emotion, EMOTION_THEMES['neutral'])

    return ChatResponse(
        reply=llm_reply,
        emotion=emotion,
        confidence=round(confidence, 3),
        theme=theme,
        quote=quote_data,
    )


@app.get('/health')
async def health():
    return {
        'status': 'healthy',
        'timestamp': datetime.datetime.utcnow().isoformat(),
    }


if __name__ == "__main__":
    import uvicorn # type: ignore
    uvicorn.run(app, host="0.0.0.0", port=8000)