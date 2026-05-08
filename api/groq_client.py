import os
import json
import asyncio
# pyrefly: ignore [missing-import]
from groq import Groq
# pyrefly: ignore [missing-import]
from dotenv import load_dotenv

load_dotenv()

_groq_api_key = os.environ.get('GROQ_API_KEY', '')
if not _groq_api_key:
    raise EnvironmentError(
        'GROQ_API_KEY is not set. Add it to your .env file.'
    )

client = Groq(api_key=_groq_api_key)


def _sync_llm_response(messages: list) -> str:
    """Synchronous inner call — run via asyncio.to_thread."""
    response = client.chat.completions.create(
        model='llama-3.3-70b-versatile',
        messages=messages,
        temperature=0.75,
        max_tokens=80,
    )
    return response.choices[0].message.content


async def get_llm_response(messages: list) -> str:
    """Non-blocking wrapper around the synchronous Groq SDK call with fallback."""
    try:
        return await asyncio.to_thread(_sync_llm_response, messages)
    except Exception as e:
        print(f"Groq API Error: {e}")
        return "I'm here for you, but I'm having a small technical hiccup. I'm still listening—tell me more about how you're feeling?"


def _sync_generate_quote(emotion: str, user_message: str,
                         seen_quotes: list) -> dict:
    """Synchronous inner call — run via asyncio.to_thread."""
    avoid = ''
    if seen_quotes:
        avoid = 'Do NOT use any of these quotes:\n'
        avoid += '\n'.join(f'- {q}' for q in seen_quotes[-10:])

    prompt = f'''
The user is feeling: {emotion}
Their message: "{user_message}"

Generate ONE meaningful short quote that could help shift their perspective.
Also write one practical physical or mental exercise they can do right now.

{avoid}

Reply ONLY in this exact JSON format (no extra text, no markdown):
{{
    "quote": "quote text here",
    "author": "Author Name",
    "exercise": "One practical thing they can do right now"
}}
'''
    response = client.chat.completions.create(
        model='llama-3.3-70b-versatile',
        messages=[{'role': 'user', 'content': prompt}],
        temperature=0.9,
        max_tokens=150,
    )
    text = response.choices[0].message.content.strip()
    # Strip any accidental markdown code fences the model adds
    text = text.replace('```json', '').replace('```', '').strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Fallback: return a safe default so the caller never crashes
        return {
            'quote': 'Every storm runs out of rain.',
            'author': 'Maya Angelou',
            'exercise': 'Take three slow, deep breaths and notice how your body relaxes.'
        }


async def generate_quote(emotion: str, user_message: str,
                         seen_quotes: list) -> dict:
    """Non-blocking wrapper around the synchronous Groq SDK call."""
    return await asyncio.to_thread(
        _sync_generate_quote, emotion, user_message, seen_quotes
    )
