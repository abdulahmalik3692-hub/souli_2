import datetime

NEGATIVE_EMOTIONS = {
    'sadness', 'grief', 'remorse', 'fear', 'nervousness',
    'anger', 'annoyance', 'disgust', 'disappointment', 'confusion',
    'disapproval', 'embarrassment',
}

# In-memory store: { (user_id, emotion): [quote_text, ...] }
_seen_quotes_cache: dict[tuple, list] = {}


def should_send_quote(emotion: str, confidence: float,
                      history: list) -> bool:
    """Return True only when a quote is warranted for this turn.

    A quote is triggered if:
    1. The current emotion is negative.
    2. The confidence is above 0.60.
    3. The user's emotion has remained the same negative emotion for the last 3 consecutive user messages
       (the current message + the last 2 user messages in history).
    4. A quote hasn't been sent in the last 3 assistant turns.
    """
    if emotion not in NEGATIVE_EMOTIONS:
        return False
    if confidence <= 0.60:
        return False

    # Get all user messages from history
    user_messages = [m for m in history if m.get('role') == 'user']

    # We need the last 2 user messages in history to exist and have the same emotion
    if len(user_messages) < 2:
        return False

    # Check if the last 2 user messages have the same emotion as the current one
    for msg in user_messages[-2:]:
        if msg.get('emotion') != emotion:
            return False

    # Don't spam: if any of the last 3 assistant turns already had a quote, skip
    recent = [m for m in history[-6:] if m.get('role') == 'assistant']
    for msg in recent[-3:]:
        if msg.get('had_quote'):
            return False
    return True


async def get_seen_quotes(user_id: str, emotion: str) -> list:
    """Return the text of the last 20 quotes sent for this emotion (in-memory)."""
    return _seen_quotes_cache.get((user_id, emotion), [])[-20:]


async def save_quote(user_id: str, emotion: str, data: dict):
    """Persist a quote record in-memory so we can avoid repetition later."""
    key = (user_id, emotion)
    if key not in _seen_quotes_cache:
        _seen_quotes_cache[key] = []
    _seen_quotes_cache[key].append(data['quote'])
    # Keep only the last 50 per user+emotion to avoid unbounded growth
    _seen_quotes_cache[key] = _seen_quotes_cache[key][-50:]
