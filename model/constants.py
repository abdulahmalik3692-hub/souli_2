# Soulify Shared Constants

NEGATIVE_EMOTIONS = {
    'sadness', 'grief', 'remorse', 'fear', 'nervousness',
    'anger', 'annoyance', 'disgust', 'disappointment', 'confusion',
    'disapproval', 'embarrassment',
}

# 28-label set from GoEmotions
ALL_EMOTIONS = {
    'admiration', 'amusement', 'anger', 'annoyance', 'approval', 'caring', 
    'confusion', 'curiosity', 'desire', 'disappointment', 'disapproval', 
    'disgust', 'embarrassment', 'excitement', 'fear', 'gratitude', 'grief', 
    'joy', 'love', 'nervousness', 'optimism', 'pride', 'realization', 
    'relief', 'remorse', 'sadness', 'surprise', 'neutral'
}

# Detection Tuning
NEGATIVE_OVERRIDE_THRESHOLD = 0.25
SMOOTHING_BOOST = 1.20
KEYWORD_BOOST = 0.12
CONTEXT_WEIGHT = 0.10

# Session Config
SESSION_TTL_MINUTES = 60
MAX_HISTORY_TURNS = 10

# Quote Config
QUOTE_CONFIDENCE_THRESHOLD = 0.85
QUOTE_COOLDOWN_TURNS = 3

# ===========================================================================
#  TYPING SPEED MODIFIER CONSTANTS (NEW)
# ===========================================================================

# Emotions that get boosted when user types FAST (>7 cps)
# Fast typing suggests agitation, excitement, or urgency
FAST_BOOST_EMOTIONS = {'anger', 'annoyance', 'fear', 'nervousness', 'excitement'}

# Emotions that get boosted when user types SLOW (<3 cps)
# Slow typing suggests heaviness, grief, or careful thought
SLOW_BOOST_EMOTIONS = {'sadness', 'grief', 'remorse', 'disappointment'}

# Slow typing + positive emotion = likely masking distress
# We penalize confidence to signal uncertainty to the caller
SLOW_TYPING_SUSPICION_THRESHOLD = 3.0      # cps
SLOW_TYPING_CONFIDENCE_PENALTY = 0.25      # Reduce confidence

# Fast typing + neutral/calm emotion = likely hidden agitation
# Return fixed confidence to trigger re-evaluation
FAST_TYPING_OVERRIDE_EMOTIONS = {'neutral', 'realization', 'curiosity', 'surprise'}
FAST_TYPING_OVERRIDE_CONFIDENCE = 0.55