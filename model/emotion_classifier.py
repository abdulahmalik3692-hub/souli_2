import warnings
import re
import time
from collections import deque
from transformers import pipeline # type: ignore

# Silence a FutureWarning emitted internally by huggingface_hub
warnings.filterwarnings(
    'ignore',
    message='.*resume_download.*',
    category=FutureWarning,
    module='huggingface_hub',
)

# ===========================================================================
#  MODEL LOADING
# ===========================================================================

# Load once at startup — top_k=None returns ALL label scores
classifier = pipeline(
    'text-classification',
    model='SamLowe/roberta-base-go_emotions',
    top_k=None
)

from model.constants import (
    NEGATIVE_EMOTIONS, NEGATIVE_OVERRIDE_THRESHOLD, 
    SMOOTHING_BOOST, KEYWORD_BOOST, CONTEXT_WEIGHT
)

# ===========================================================================
#  SESSION STATE
# ===========================================================================

session_windows: dict[str, dict] = {}   # { session_id: {'data': deque, 'last_seen': float} }
emotion_history: dict[str, dict] = {}   # { session_id: {'data': deque, 'last_seen': float} }

def _cleanup_stale_sessions():
    """Remove sessions older than 2 hours to prevent memory leaks."""
    now = time.time()
    stale_threshold = 2 * 60 * 60  # 2 hours in seconds
    
    for sid in list(session_windows.keys()):
        if now - session_windows[sid]['last_seen'] > stale_threshold:
            del session_windows[sid]
            
    for sid in list(emotion_history.keys()):
        if now - emotion_history[sid]['last_seen'] > stale_threshold:
            del emotion_history[sid]

# ===========================================================================
#  SARCASM & MASKING DETECTION
# ===========================================================================

SARCASM_PATTERNS = [
    (r'\boh\s+(great|wonderful|fantastic|perfect|lovely|nice)\b', 'annoyance'),
    (r'\bjust\s+what\s+i\s+(needed|wanted)\b', 'annoyance'),
    (r'\byeah[,\s]*\s*(right|sure|okay|ok|fine)\b', 'annoyance'),
    (r'\bwonderful[,\s]*\s*(another|more|again|now)\b', 'annoyance'),
    (r'\b(total|totally|completely|absolutely)\s+fine\b', 'sadness'),
    (r'\bi\s+(am|m)\s+fine[.,\s]*\s*(really|trust me|don\'t worry|it\'s nothing|forget it)\b', 'sadness'),
    (r'\bfine[.,\s]*\s*everything\s+(is\s+)?fine\b', 'sadness'),
    (r'\bnot\s+(exactly|really|quite)\s+(happy|thrilled|excited|pleased|overjoyed)\b', 'disappointment'),
    (r'\bso\s+(happy|glad|excited)\s+(about|for)\s+this[.,\s]*\s*(not|never|hate|ugh)\b', 'annoyance'),
]

def detect_sarcasm(text: str) -> tuple[str, float] | None:
    """Returns (emotion, base_confidence) if sarcasm/masking detected."""
    text_lower = text.lower()
    for pattern, emotion in SARCASM_PATTERNS:
        if re.search(pattern, text_lower):
            return emotion, 0.75
    return None

# ===========================================================================
#  TEXT PREPROCESSING
# ===========================================================================

CONTRACTIONS = {
    "i'm": "i am", "don't": "do not", "can't": "cannot",
    "won't": "will not", "isn't": "is not", "aren't": "are not",
    "wasn't": "was not", "weren't": "were not", "hasn't": "has not",
    "haven't": "have not", "hadn't": "had not", "doesn't": "does not",
    "didn't": "did not", "couldn't": "could not", "shouldn't": "should not",
    "wouldn't": "would not", "i've": "i have", "you've": "you have",
    "we've": "we have", "they've": "they have", "i'll": "i will",
    "you'll": "you will", "we'll": "we will", "they'll": "they will",
    "i'd": "i would", "you'd": "you would", "he'd": "he would",
    "she'd": "she would", "we'd": "we would", "they'd": "they would",
    "it's": "it is", "that's": "that is", "what's": "what is",
    "who's": "who is", "where's": "where is", "how's": "how is",
    "let's": "let us", "there's": "there is", "here's": "here is",
}

SLANG_MAP = {
    "im": "i am", "ive": "i have", "id": "i would",
    "cant": "cannot", "dont": "do not", "wont": "will not",
    "didnt": "did not", "doesnt": "does not", "isnt": "is not",
    "wasnt": "was not", "havent": "have not", "hasnt": "has not",
    "couldnt": "could not", "shouldnt": "should not",
    "wouldnt": "would not",
    "rn": "right now", "ngl": "not going to lie",
    "tbh": "to be honest", "imo": "in my opinion",
    "idk": "i do not know", "smh": "shaking my head",
    "omg": "oh my god", "nvm": "never mind",
    "pls": "please", "plz": "please", "thx": "thanks",
    "ty": "thank you", "bf": "boyfriend", "gf": "girlfriend",
    "gonna": "going to", "wanna": "want to", "gotta": "got to",
    "kinda": "kind of", "sorta": "sort of", "prolly": "probably",
    "cuz": "because", "bcuz": "because", "coz": "because",
    "ur": "your", "u": "you", "r": "are",
    "luv": "love", "gud": "good", "bt": "but",
    "hw": "how", "abt": "about", "tho": "though",
    "w/": "with", "w/o": "without",
}

EMOJI_MAP = {
    '😢': ' sad ', '😭': ' very sad crying ', '😞': ' disappointed ',
    '😔': ' sad down ', '🥺': ' sad pleading ', '😿': ' sad ',
    '😡': ' angry ', '🤬': ' very angry ', '😠': ' angry ',
    '💢': ' angry ', '👿': ' angry ',
    '😨': ' scared afraid ', '😰': ' anxious worried ', '😱': ' terrified ',
    '😳': ' embarrassed shocked ',
    '😊': ' happy ', '😄': ' happy joyful ', '🥰': ' love happy ',
    '😍': ' love adore ', '❤️': ' love ', '💕': ' love ',
    '🥳': ' excited celebrating ', '🎉': ' excited joy ',
    '😎': ' confident proud ', '💪': ' strong proud ',
    '🤔': ' thinking curious ', '😐': ' neutral ',
    '😤': ' frustrated annoyed ', '🙄': ' annoyed ',
    '😮': ' surprised ', '😲': ' surprised shocked ',
    '🤗': ' caring warm ', '🙏': ' grateful thankful ',
    '😌': ' relieved calm ', '🤮': ' disgusted ',
    '💔': ' heartbroken sad grief ',
}

def preprocess_text(text: str) -> str:
    for emoji, replacement in EMOJI_MAP.items():
        text = text.replace(emoji, replacement)
    text = text.lower().strip()
    for contraction, expansion in CONTRACTIONS.items():
        text = text.replace(contraction, expansion)
    words = text.split()
    words = [SLANG_MAP.get(w, w) for w in words]
    text = ' '.join(words)
    text = text.encode('ascii', 'ignore').decode('ascii')
    text = re.sub(r'\s+', ' ', text).strip()
    return text

EMOTION_KEYWORDS = {
    'sadness':        {'sad', 'unhappy', 'depressed', 'down', 'blue', 'miserable',
                       'heartbroken', 'cry', 'crying', 'tears', 'lonely', 'alone',
                       'empty', 'hopeless', 'devastated', 'broken', 'hurting',
                       'fine', 'okay', 'ok', 'alright', 'nothing', 'whatever', 'numb'},
    'grief':          {'grief', 'mourning', 'loss', 'bereaved', 'grieving',
                       'passed away', 'died', 'death', 'funeral', 'gone forever'},
    'remorse':        {'sorry', 'regret', 'guilty', 'guilt', 'ashamed',
                       'remorseful', 'apologize', 'mistake', 'fault'},
    'fear':           {'scared', 'afraid', 'terrified', 'frightened', 'panic',
                       'dread', 'petrified', 'horrified', 'fearful', 'phobia'},
    'nervousness':    {'nervous', 'anxious', 'worried', 'uneasy', 'tense',
                       'jittery', 'restless', 'stressed', 'overwhelmed',
                       'panicking', 'overthinking', 'anxiety', 'exam', 'interview'},
    'anger':          {'angry', 'furious', 'mad', 'rage', 'pissed', 'livid',
                       'outraged', 'infuriated', 'hostile', 'enraged', 'irate', 'hate',
                       'betrayed', 'betrayal', 'backstabbed', 'cheated', 'used',
                       'manipulated', 'lied to', 'deceived', 'stabbed in the back'},
    'annoyance':      {'annoyed', 'irritated', 'bugged', 'bothered', 'nagging',
                       'pestering', 'tiresome', 'ugh', 'argh', 'sarcastic', 'sarcasm'},
    'disgust':        {'disgusted', 'gross', 'revolting', 'sickening',
                       'nauseating', 'repulsive', 'vile', 'nasty', 'eww', 'disgusting'},
    'disappointment': {'disappointed', 'letdown', 'let down', 'failed',
                       'failure', 'unfair', 'unsatisfied', 'expected more'},
    'confusion':      {'confused', 'lost', 'uncertain', 'unsure', 'puzzled',
                       'bewildered', 'perplexed', 'disoriented', 'no idea'},
    'disapproval':    {'wrong', 'disapprove', 'disagree', 'unacceptable',
                       'inappropriate', 'bad idea', 'terrible'},
    'embarrassment':  {'embarrassed', 'humiliated', 'ashamed', 'mortified',
                       'awkward', 'cringe', 'uncomfortable'},
    'joy':            {'happy', 'joyful', 'wonderful', 'amazing', 'fantastic',
                       'great', 'blessed', 'delighted', 'cheerful', 'ecstatic',
                       'elated', 'blissful', 'overjoyed'},
    'excitement':     {'excited', 'pumped', 'thrilled', 'hyped', 'stoked',
                       'eager', 'cannot wait', 'can not wait', 'psyched'},
    'love':           {'love', 'adore', 'cherish', 'affection', 'romantic',
                       'crush', 'soulmate', 'passionate', 'devoted', 'sweetheart'},
    'amusement':      {'funny', 'hilarious', 'laughing', 'amusing', 'humorous',
                       'comedy', 'joke', 'lmao', 'haha', 'lol'},
    'desire':         {'want', 'wish', 'desire', 'crave', 'yearn', 'longing',
                       'miss', 'missing'},
    'admiration':     {'admire', 'respect', 'inspired', 'impressed', 'incredible',
                       'look up to', 'role model'},
    'caring':         {'care', 'caring', 'concerned', 'worry about',
                       'compassion', 'empathy', 'hope you'},
    'approval':       {'agree', 'approve', 'support', 'endorse', 'good job',
                       'well done', 'nice work', 'exactly'},
    'gratitude':      {'grateful', 'thankful', 'appreciate', 'thanks',
                       'thank you', 'blessed'},
    'optimism':       {'hopeful', 'optimistic', 'positive', 'bright',
                       'promising', 'looking forward', 'better days'},
    'pride':          {'proud', 'accomplished', 'achieved', 'success',
                       'triumphant', 'nailed it', 'killed it'},
    'curiosity':      {'curious', 'wondering', 'interested', 'intrigued',
                       'fascinated', 'how does', 'what if'},
    'realization':    {'realized', 'understand', 'figured out', 'discovered',
                       'noticed', 'epiphany', 'now i see', 'makes sense'},
    'surprise':       {'surprised', 'shocked', 'astonished', 'amazed',
                       'stunned', 'unexpected', 'wow', 'unbelievable', 'no way'},
    'relief':         {'relieved', 'relief', 'finally', 'weight off',
                       'phew', 'thank goodness', 'glad it is over'},
}

def _compute_keyword_boosts(text: str) -> dict:
    text_lower = text.lower()
    words_set = set(text_lower.split())
    boosts = {}
    for emotion, keywords in EMOTION_KEYWORDS.items():
        match_count = 0
        for kw in keywords:
            if ' ' in kw:
                if kw in text_lower:
                    match_count += 1
            else:
                if kw in words_set:
                    match_count += 1
        if match_count > 0:
            # Stronger boost for disgust — words are unambiguous
            multiplier = 2.0 if emotion == 'disgust' else 1.0
            boost = KEYWORD_BOOST * multiplier * (1.0 - 0.5 ** match_count)
            boosts[emotion] = round(boost, 4)
    return boosts

def recalibrate_confidence(raw_score: float) -> float:
    if raw_score >= 0.80:
        return min(0.95 + (raw_score - 0.80) * 0.20, 0.99)
    elif raw_score >= 0.50:
        return 0.78 + (raw_score - 0.50) * (0.17 / 0.30)
    elif raw_score >= 0.30:
        return 0.60 + (raw_score - 0.30) * (0.18 / 0.20)
    elif raw_score >= 0.15:
        return 0.45 + (raw_score - 0.15) * (0.15 / 0.15)
    else:
        return max(raw_score * 3.0, 0.10)

# ===========================================================================
#  MAIN DETECTION FUNCTION
# ===========================================================================

def detect_emotion(new_message: str, session_id: str) -> dict:
    now = time.time()
    
    # Run cleanup periodically (approx 1 in 100 requests)
    if now % 100 < 1:
        _cleanup_stale_sessions()
        
    if session_id not in session_windows:
        session_windows[session_id] = {'data': deque(maxlen=3), 'last_seen': now}
    session_windows[session_id]['data'].append(new_message)
    session_windows[session_id]['last_seen'] = now

    # ── SARCASM / MASKING DETECTION ─────────────────────────────────────
    sarcasm = detect_sarcasm(new_message)
    if sarcasm:
        sarcasm_emotion, base_conf = sarcasm
        cleaned = preprocess_text(new_message)
        all_scores = classifier(cleaned[:512])[0]
        
        # Align with classifier if possible, otherwise use rule-based
        matching = [s for s in all_scores if s['label'] == sarcasm_emotion]
        if matching:
            confidence = max(matching[0]['score'] + 0.20, base_conf)
        else:
            confidence = base_conf
        
        confidence = recalibrate_confidence(min(confidence, 1.0))
        
        # History smoothing
        if session_id not in emotion_history:
            emotion_history[session_id] = {'data': deque(maxlen=5), 'last_seen': now}
        history_obj = emotion_history[session_id]
        history_obj['last_seen'] = now
        history = history_obj['data']
        if history:
            if history[-1]['emotion'] == sarcasm_emotion:
                confidence = confidence * SMOOTHING_BOOST
            if len(history) >= 2:
                recent_emotions = [h['emotion'] for h in list(history)[-3:]]
                if recent_emotions.count(sarcasm_emotion) >= 2:
                    confidence += CONTEXT_WEIGHT
        
        confidence = recalibrate_confidence(min(confidence, 1.0))
        history.append({'emotion': sarcasm_emotion, 'confidence': confidence})
        return {'emotion': sarcasm_emotion, 'confidence': round(confidence, 3)}

    cleaned = preprocess_text(new_message)
    all_scores = classifier(cleaned[:512])[0]
    keyword_boosts = _compute_keyword_boosts(cleaned)
    
    # Strong disgust override for explicit words
    explicit_disgust = {'revolting', 'repulsive', 'vile', 'nauseating', 'sickening', 'disgusting'}
    if any(w in cleaned for w in explicit_disgust):
        for item in all_scores:
            if item['label'] == 'disgust':
                item['score'] = max(item['score'], 0.60)
    
    if keyword_boosts:
        for item in all_scores:
            if item['label'] in keyword_boosts:
                item['score'] += keyword_boosts[item['label']]
    
    result_sorted = sorted(all_scores, key=lambda x: x['score'], reverse=True)
    top = result_sorted[0]
    emotion = top['label']
    confidence = top['score']
    
    if emotion not in NEGATIVE_EMOTIONS:
        for item in result_sorted[1:]:
            if item['label'] in NEGATIVE_EMOTIONS and item['score'] >= NEGATIVE_OVERRIDE_THRESHOLD:
                emotion = item['label']
                confidence = item['score']
                break
    
    if session_id not in emotion_history:
        emotion_history[session_id] = {'data': deque(maxlen=5), 'last_seen': now}
    history_obj = emotion_history[session_id]
    history_obj['last_seen'] = now
    history = history_obj['data']
    if history:
        if history[-1]['emotion'] == emotion:
            confidence = confidence * SMOOTHING_BOOST
        if len(history) >= 2:
            recent_emotions = [h['emotion'] for h in list(history)[-3:]]
            if recent_emotions.count(emotion) >= 2:
                confidence += CONTEXT_WEIGHT
    
    confidence = recalibrate_confidence(min(confidence, 1.0))
    history.append({'emotion': emotion, 'confidence': confidence})
    return {'emotion': emotion, 'confidence': round(confidence, 3)}