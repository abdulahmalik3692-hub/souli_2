import sys, asyncio, os, uuid

# Ensure the project root is always on the path, regardless of CWD
_root = os.path.dirname(os.path.abspath(__file__))
if _root not in sys.path:
    sys.path.insert(0, _root)

from model.emotion_classifier import detect_emotion
from model.behavior import apply_typing_modifier
from model.emotion_colors import EMOTION_THEMES
from api.prompt_engine import build_prompt
from api.groq_client import get_llm_response, generate_quote
from api.quote_manager import should_send_quote, get_seen_quotes, save_quote

history: list = []
session_id = str(uuid.uuid4())
user_id    = str(uuid.uuid4())
print(f'Session started: {session_id[:8]}...')


async def chat(msg: str, spd: float = 5.0):
    # 1. Detect emotion (sync model call, runs in thread pool)
    er = await asyncio.to_thread(detect_emotion, msg, session_id)
    em = er['emotion']
    cf = apply_typing_modifier(em, er['confidence'], spd)

    # 2. Build prompt and call LLM
    rp = await get_llm_response(build_prompt(msg, em, cf, history))

    # 3. Optionally generate and save a quote
    qd = None
    if should_send_quote(em, cf, history):
        seen = await get_seen_quotes(user_id, em)
        qd = await generate_quote(em, msg, seen)
        await save_quote(user_id, em, qd)
        # Combine the quote with the main response text
        rp += f'\n\n"{qd["quote"]}" — {qd["author"]} (Try this: {qd["exercise"]})'

    # 4. Update history
    history.append({'role': 'user', 'content': msg, 'emotion': em})
    history.append({'role': 'assistant', 'content': rp, 'had_quote': qd is not None})

    # 5. Print output
    th = EMOTION_THEMES.get(em, EMOTION_THEMES['neutral'])
    print(f'\n[{em.upper()} | {round(cf, 2)} | {th["accent"]}]\nSoulify: {rp}')
    print()


async def main():
    print('\n=== SOULIFY LIVE CHAT (type quit to exit) ===\n')
    while True:
        msg = input('You: ').strip()
        if msg.lower() in ['quit', 'exit', 'q']:
            break
        if msg:
            await chat(msg)


if __name__ == '__main__':
    asyncio.run(main())
