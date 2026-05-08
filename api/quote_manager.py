import datetime
from database.db import user_quotes

NEGATIVE_EMOTIONS = {
    'sadness', 'grief', 'remorse', 'fear', 'nervousness',
    'anger', 'annoyance', 'disgust', 'disappointment', 'confusion',
    'disapproval', 'embarrassment',
}


def should_send_quote(emotion: str, confidence: float,
                      history: list) -> bool:
    """Return True only when a quote is warranted for this turn."""
    if emotion not in NEGATIVE_EMOTIONS:
        return False
    if confidence <= 0.60:
        return False
    # Don't spam: if any of the last 3 assistant turns already had a quote, skip
    recent = [m for m in history[-6:] if m.get('role') == 'assistant']
    for msg in recent[-3:]:
        if msg.get('had_quote'):
            return False
    return True


async def get_seen_quotes(user_id: str, emotion: str) -> list:
    """Return the text of the last 20 quotes sent for this emotion."""
    try:
        cursor = user_quotes.find(
            {'user_id': user_id, 'emotion': emotion},
            {'quote_text': 1}
        ).sort('sent_at', -1).limit(20)
        docs = await cursor.to_list(20)
        return [d['quote_text'] for d in docs]
    except Exception:
        # MongoDB unreachable — return empty so the quote still generates
        return []


async def save_quote(user_id: str, emotion: str, data: dict):
    """Persist a quote record so we can avoid repetition later."""
    try:
        await user_quotes.insert_one({
            'user_id':    user_id,
            'emotion':    emotion,
            'quote_text': data['quote'],
            'author':     data['author'],
            'exercise':   data['exercise'],
            'sent_at':    datetime.datetime.utcnow()
        })
    except Exception:
        # MongoDB unreachable — silently skip persistence
        pass

