# ─────────────────────────────────────────────────────────────────────
#  SOULIFY — COLOR PSYCHOLOGY ENGINE
#  All 27 GoEmotions + neutral = 28 labels
#
#  PRINCIPLE:
#    Negative emotion detected → show the HEALING color that
#    color psychology says will shift that state toward positive.
#    Positive emotion detected → show the AMPLIFYING color that
#    sustains and deepens the positive state.
#
#  Each entry: { bg, accent, text }
#    bg     = full-screen background (soft, low-saturation)
#    accent = buttons / highlights / avatar ring (vibrant)
#    text   = primary text color (high contrast on bg)
# ─────────────────────────────────────────────────────────────────────


EMOTION_THEMES = {

    # ================================================================
    #  NEGATIVE → HEALING  (Directly counteracting the negative state)
    # ================================================================

    # ── SADNESS / GRIEF / REMORSE ───────────────────────────────────
    # Psychology: Sunshine Gold (High-frequency yellow) stimulates 
    # serotonin and mimics the antidepressant effect of sunlight.
    'sadness':        {'bg': '#FFFDF0', 'accent': '#FFD700', 'text': '#8B7300'},
    'grief':          {'bg': '#FFFDF0', 'accent': '#FFD700', 'text': '#8B7300'},
    'remorse':        {'bg': '#FFFDF0', 'accent': '#FFD700', 'text': '#8B7300'},

    # ── FEAR / NERVOUSNESS ──────────────────────────────────────────
    # Psychology: Deep Mint Green is the most "grounding" color. 
    # It signals safety/nature and lowers the heart rate instantly.
    'fear':           {'bg': '#F0FFF4', 'accent': '#38A169', 'text': '#22543D'},
    'nervousness':    {'bg': '#F0FFF4', 'accent': '#38A169', 'text': '#22543D'},

    # ── ANGER / DISGUST / DISAPPROVAL ───────────────────────────────
    # Psychology: Arctic Blue (Short-wave blue) is the physical 
    # opposite of red arousal. It cools the brain and reduces impulses.
    'anger':          {'bg': '#F0F5FF', 'accent': '#3182CE', 'text': '#2A4365'},
    'annoyance':      {'bg': '#F0F5FF', 'accent': '#3182CE', 'text': '#2A4365'},
    'disgust':        {'bg': '#F0F5FF', 'accent': '#3182CE', 'text': '#2A4365'},
    'disapproval':    {'bg': '#F0F5FF', 'accent': '#3182CE', 'text': '#2A4365'},

    # ── CONFUSION ───────────────────────────────────────────────────
    # Psychology: Clarity Lavender assists in logical/emotional 
    # integration. Helps the mind bridge the "left-right" brain gap.
    'confusion':      {'bg': '#FAF5FF', 'accent': '#805AD5', 'text': '#44337A'},

    # ── DISAPPOINTMENT ──────────────────────────────────────────────
    # Psychology: Ocean Teal provides depth and perspective. It 
    # encourages "zooming out" from a loss to see the bigger picture.
    'disappointment': {'bg': '#E6FFFA', 'accent': '#319795', 'text': '#234E52'},

    # ── EMBARRASSMENT ───────────────────────────────────────────────
    # Psychology: Rose Quartz reduces cortisol levels and encourages 
    # self-kindness, easing the physical heat of embarrassment.
    'embarrassment':  {'bg': '#FFF5F7', 'accent': '#D53F8C', 'text': '#702459'},


    # ================================================================
    #  POSITIVE → AMPLIFY  (Energizing and deepening the good state)
    # ================================================================

    # ── JOY / EXCITEMENT / AMUSEMENT ────────────────────────────────
    # Psychology: Solar Orange/Amber creates a sense of "best mood."
    # It is social, loud, and high-energy—the color of celebration.
    'joy':            {'bg': '#FFFAF0', 'accent': '#ED8936', 'text': '#7B341E'},
    'excitement':     {'bg': '#FFFAF0', 'accent': '#ED8936', 'text': '#7B341E'},
    'amusement':      {'bg': '#FFFAF0', 'accent': '#ED8936', 'text': '#7B341E'},

    # ── LOVE / DESIRE / CARING ──────────────────────────────────────
    # Psychology: Radiant Magenta signifies deep emotional connection 
    # and passion. It makes the user feel "seen" and cherished.
    'love':           {'bg': '#FFF5F5', 'accent': '#E53E3E', 'text': '#742A2A'},
    'desire':         {'bg': '#FFF5F5', 'accent': '#E53E3E', 'text': '#742A2A'},
    'caring':         {'bg': '#FFF5F5', 'accent': '#E53E3E', 'text': '#742A2A'},

    # ── ADMIRATION / APPROVAL ───────────────────────────────────────
    # Psychology: Royal Indigo sustains feelings of respect and 
    # high-worth. It adds a layer of "prestige" to the achievement.
    'admiration':     {'bg': '#EBF4FF', 'accent': '#4299E1', 'text': '#2B6CB0'},
    'approval':       {'bg': '#EBF4FF', 'accent': '#4299E1', 'text': '#2B6CB0'},

    # ── GRATITUDE / OPTIMISM / PRIDE ────────────────────────────────
    # Psychology: Emerald Growth represents flourishing success. 
    # It tells the user "you are on the right path."
    'gratitude':      {'bg': '#F0FFF4', 'accent': '#48BB78', 'text': '#22543D'},
    'optimism':       {'bg': '#F0FFF4', 'accent': '#48BB78', 'text': '#22543D'},
    'pride':          {'bg': '#F0FFF4', 'accent': '#48BB78', 'text': '#22543D'},


    # ================================================================
    #  TRANSITIONAL → GUIDE  (Surprise and Curiosity)
    # ================================================================

    'curiosity':      {'bg': '#FAF5FF', 'accent': '#9F7AEA', 'text': '#553C9A'},
    'realization':    {'bg': '#FAF5FF', 'accent': '#9F7AEA', 'text': '#553C9A'},
    'surprise':       {'bg': '#FAF5FF', 'accent': '#9F7AEA', 'text': '#553C9A'},
    'relief':         {'bg': '#E6FFFA', 'accent': '#38B2AC', 'text': '#285E61'},


    # ================================================================
    #  NEUTRAL → BALANCED  (Centering)
    # ================================================================

    'neutral':        {'bg': '#F7FAFC', 'accent': '#A0AEC0', 'text': '#2D3748'},
}
