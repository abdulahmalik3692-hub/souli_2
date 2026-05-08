from model.constants import (
    FAST_BOOST_EMOTIONS,
    SLOW_BOOST_EMOTIONS,
    SLOW_TYPING_SUSPICION_THRESHOLD,
    SLOW_TYPING_CONFIDENCE_PENALTY,
    FAST_TYPING_OVERRIDE_EMOTIONS,
    FAST_TYPING_OVERRIDE_CONFIDENCE,
)

def apply_typing_modifier(emotion: str, confidence: float,
                          typing_speed: float) -> float:
    """
    typing_speed: characters per second measured in React frontend.
    Typical ranges: slow < 3 cps, normal 3-7 cps, fast > 7 cps.
    
    Handles speed-emotion contradictions:
    - Slow typing + positive emotion = likely masking sadness/distress
    - Fast typing + neutral/calm emotion = likely agitation
    """
    
    # ── CONTRADICTION DETECTION ─────────────────────────────────────────
    # Slow typing + forced positivity = suspect suppressed negative emotion
    if (typing_speed < SLOW_TYPING_SUSPICION_THRESHOLD and 
        emotion in {'joy', 'approval', 'admiration', 'optimism', 'gratitude'}):
        confidence = max(confidence - SLOW_TYPING_CONFIDENCE_PENALTY, 0.45)
        return round(confidence, 3)
    
    # Fast typing + calm/neutral = likely hidden agitation
    if (typing_speed > 8 and 
        emotion in FAST_TYPING_OVERRIDE_EMOTIONS):
        return round(FAST_TYPING_OVERRIDE_CONFIDENCE, 3)
    
    # ── STANDARD BOOSTS ──────────────────────────────────────────────────
    boost = 0.0
    if typing_speed > 7 and emotion in FAST_BOOST_EMOTIONS:
        boost = 0.08   # fast typing + agitated emotion
    elif typing_speed < 3 and emotion in SLOW_BOOST_EMOTIONS:
        boost = 0.08   # slow typing + sad emotion
    
    return round(min(confidence + boost, 0.99), 3)