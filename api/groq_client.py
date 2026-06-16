"""Groq LLM client for Soulify.

Handles all communication with the Groq API including:
- Building contextual instructions based on conversation state
- Cleaning and validating LLM responses
- Graceful fallback when the API is unavailable
"""

import os
import re
import asyncio
import random
import logging

from groq import Groq
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# ── Groq Client Setup ─────────────────────────────────────────────────────

_groq_api_key = os.environ.get('GROQ_API_KEY', '')
if not _groq_api_key:
    raise EnvironmentError('GROQ_API_KEY is not set.')

client = Groq(api_key=_groq_api_key)

MODEL_NAME = 'llama-3.3-70b-versatile'

# Track API calls for debugging
_api_call_count = 0

# ── Prophet/Story Names (single source of truth) ──────────────────────────

STORY_NAMES = [
    'Prophet Ayub', 'Prophet Yusuf', 'Prophet Musa', 'Prophet Muhammad',
    'Prophet Nuh', 'Prophet Ibrahim', 'Prophet Yaqub', 'Prophet Yunus',
    'Nelson Mandela', 'Malala', 'Viktor Frankl', 'Khadijah',
]

# ── Banned Response Patterns (compiled once for performance) ──────────────

_BANNED_PATTERNS = [
    re.compile(p) for p in [
        r"[Ii]n (the|this) (stillness|quiet) of the night[,.]?\s*",
        r"[Tt]he morning light[^.]*\.\s*",
        r"[Ee]verything (will )?look[s]? different in the morning[^.]*\.\s*",
        r"[Ww]hen the morning comes[^.]*\.\s*",
        r"[Ii] can feel the[^.]*\.\s*",
        r"[Ll]et'?s start this morning fresh[^.]*\.\s*",
        r"[Ww]hat'?s one thing you'?re? grateful for[^.]*\?",
        r"[Ii]t'?s okay to question[^.]*\.\s*",
        r"[Tt]hat'?s what makes us human[^.]*\.\s*",
        r"[Tt]oday'?s? (a |is )?(fresh start|new day|blank page)[^.]*\.\s*",
        r"[Ff]resh start[^.]*\.\s*",
        r"[Ii]'?m so proud of you[^.]*\.\s*",
        r"[Tt]hink of \d+ things[^.]*\.\s*",
        r"[Ll]et'?s begin with gratitude[^.]*\.\s*",
        r"[Ss]hifting your perspective[^.]*\.\s*",
        r"[Bb]lank page[^.]*\.\s*",
        r"[Ii]n this quiet night[^.]*\.\s*",
        r"[Ll]ate at night[^.]*\.\s*",
        r"[Tt]his darkness will pass[^.]*\.\s*",
        r"[Jj]ust breathe[^.]*\.\s*",
        r"[Bb]reathe and trust[^.]*\.\s*",
        r"[Ww]hen it can feel (the )?darkest[^.]*\.\s*",
        r"[Ww]hen it can feel really lonely[^.]*\.\s*",
        r"[Gg]ood morning[^.]*\.\s*",
        r"[Ss]tart today with[^.]*\.\s*",
        r"[Tt]ry making today[^.]*\.\s*",
        r"[Ww]hat'?s? the first (good )?thing[^.]*\.\s*",
        r"[Ll]ight up (the )?rest of your day[^.]*\.\s*",
        r"[Nn]ew day[^.]*\.\s*",
        r"[Bb]egin with shukr[^.]*\.\s*",
        r"[Ss]tart with shukr[^.]*\.\s*",
        r"[Tt]ake a deep breath[^.]*\.\s*",
        r"[Ss]tart(ing)? (the|this|your) day[^.]*\.\s*",
        r"[Nn]ew morning[^.]*\.\s*",
        r"[Nn]ew page to write[^.]*\.\s*",
        r"[Ww]aiting to happen[^.]*\.\s*",
        r"[Ll]et'?s start[^.]*\.\s*",
        r"[Aa]llah loves all [Hh]is creations[^.]*\.\s*",
        r"[Aa]llah'?s? plan is perfect[^.]*\.\s*",
        r"[Ee]verything happens for a reason[^.]*\.\s*",
        r"[Jj]ust know you'?re? not alone[^.]*\.\s*",
        r"[Tt]onight feels? (extra |really )?(heavy|hard)[^.]*\.\s*",
        r"[Dd]arkness (of night|can make)[^.]*\.\s*",
        r"[Ii]t'?s (completely )?understandable[^.]*\.\s*",
    ]
]

# Markers that indicate the model echoed its instructions back
_INSTRUCTION_MARKERS = [
    'You are Souli', 'Responding now:', 'Rules:',
    'ALLAH MENTIONED', 'Feel what',
]

_MULTI_SPACE = re.compile(r'  +')

# ── Message Type Keywords ─────────────────────────────────────────────────

_TYPE_KEYWORDS = {
    'gratitude': ['thanks', 'thank you', 'shukria', 'jazakallah',
                  'feel better', 'helped me', 'feel good now',
                  'you helped', 'appreciate'],
    'goodbye':   ['bye', 'later', 'goodbye', 'good night',
                  'will talk', 'see you', 'gtg'],
    'pushback':  ['shutup', 'shut up', 'go away', 'leave me'],
    'deflecting': ['never mind', 'forget it', 'leave it',
                   'doesnt matter', "doesn't matter"],
    'dark_humor': ['haha', 'lol', 'hehe', 'but fine',
                   'its fine', "it's fine", 'but okay'],
    'criticism':  ['shame on you', 'worst', 'useless',
                   'not helping', 'you failed'],
}

_ALLAH_KEYWORDS = ['allah', 'god', 'rab', 'rabb', 'khuda', 'almighty']

# ── Helper Functions ──────────────────────────────────────────────────────


def _get_last_user_message(messages: list) -> str:
    """Extract the last user message from the conversation."""
    for m in reversed(messages):
        if m.get('role') == 'user':
            return m.get('content', '')
    return ''


def _get_turn_count(messages: list) -> int:
    """Count the number of user turns in the conversation."""
    return sum(1 for m in messages if m.get('role') == 'user')


def _count_used_stories(messages: list) -> int:
    """Count how many unique Prophet/person stories have been used."""
    used = set()
    for m in messages:
        if m.get('role') == 'assistant':
            content = m.get('content', '')
            for name in STORY_NAMES:
                if name in content:
                    used.add(name)
    return len(used)


def _get_used_names(messages: list) -> str:
    """Get a comma-separated string of used story names."""
    used = []
    for m in messages:
        if m.get('role') == 'assistant':
            content = m.get('content', '')
            for name in STORY_NAMES:
                if name in content and name not in used:
                    used.append(name)
    return ', '.join(used) if used else 'none'


def _detect_allah_mention(message: str) -> bool:
    """Check if the message mentions Allah/God."""
    msg_lower = message.lower()
    return any(k in msg_lower for k in _ALLAH_KEYWORDS)


def _detect_type(message: str) -> str:
    """Classify the message type (gratitude, goodbye, pushback, etc.)."""
    msg = message.lower().strip()
    for msg_type, keywords in _TYPE_KEYWORDS.items():
        if any(w in msg for w in keywords):
            return msg_type
    return 'normal'


# ── Instruction Builder ───────────────────────────────────────────────────


def _build_instruction(messages: list) -> str:
    """Build contextual behavioral instructions based on conversation state.

    Analyzes conversation history to determine:
    - Whether shukr/gratitude has been overused
    - Turn count and appropriate response strategy
    - Story usage tracking
    - Allah mention handling
    """
    # Check for shukr overuse in recent responses
    recent_assistant = [
        m.get('content', '') for m in messages[-6:]
        if m.get('role') == 'assistant'
    ]
    shukr_overused = sum(
        1 for m in recent_assistant
        if any(w in m.lower() for w in ['shukr', 'gratitude', 'grateful'])
    ) >= 2

    turn = _get_turn_count(messages)
    last = _get_last_user_message(messages)
    msg = last.lower()
    used = _count_used_stories(messages)
    used_names = _get_used_names(messages)
    allah = _detect_allah_mention(last)
    msg_type = _detect_type(last)

    # ── Special message types (short, direct responses) ────────────────
    type_responses = {
        'gratitude':  "They thanked me. Receive it warmly. 1 sentence. Casual like a friend. No story.",
        'goodbye':    "They are leaving. 1 warm casual line. Like 'Take care yaar. Always here.'",
        'pushback':   "They pushed me away. Respect it. 1 short line only.",
        'deflecting': "They pulled back. Hold door open. 1 casual sentence. Like 'Okay, here whenever you want.'",
        'dark_humor': "They used dark humor. Match the lightness first. Then gently go one layer deeper with one real question.",
        'criticism':  "They criticized me. Stay humble and warm. 1 sentence.",
    }
    if msg_type in type_responses:
        return type_responses[msg_type]

    # ── Story usage rules ──────────────────────────────────────────────
    if used == 0:
        story_rule = (
            "No stories used yet. You can use ONE story from the pool "
            "if it genuinely mirrors their exact situation. Save it for "
            "a moment that truly calls for it."
        )
    elif used == 1:
        story_rule = f"Story already used: {used_names}. No more stories now. Just be their warm friend."
    else:
        story_rule = f"Stories used: {used_names}. No more stories. Just be present and real."

    # ── Turn-based strategy ────────────────────────────────────────────
    if turn <= 1:
        turn_part = "Very early. Just listen. Ask one warm casual question. No stories yet."
    elif turn == 2:
        turn_part = "You know a little. Be warm and natural. No story yet."
    else:
        # Check for persistent negativity
        negative_count = sum(
            1 for m in messages
            if m.get('role') == 'user'
            and any(w in m.get('content', '').lower()
                    for w in ['cant', "can't", 'nothing', 'why me', 'everyone',
                              'against', 'lonely', 'stuck', 'hopeless'])
        )

        if negative_count >= 1 and used == 0:
            turn_part = (
                f"Turn {turn + 1}. This person has been struggling through "
                f"multiple messages. Now is the right moment to use ONE "
                f"Prophet story that genuinely mirrors their pain. Feel with "
                f"them first — one sentence. Then bring the story briefly. "
                f"Connect it to their exact situation. {story_rule}"
            )
        else:
            turn_part = (
                f"Turn {turn + 1}. You know them well. "
                f"Be their closest friend. {story_rule}"
            )

    # ── Allah mention handling ─────────────────────────────────────────
    allah_part = ""
    if allah:
        if used < 1:
            allah_part = (
                "\nALLAH MENTIONED: Sacred moment. Bring His love through "
                "one real story. Acknowledge first. Remind them hopelessness "
                "is haram and Allah never abandons those who hold on."
            )
        else:
            allah_part = (
                "\nALLAH MENTIONED: No more stories. Bring His love through "
                "real warm words. Remind them that a heart still asking has "
                "not lost faith. When you take one step toward Allah He comes running."
            )

    return (
        f"You are Souli. Spiritual buddy. WhatsApp friend tone.\n"
        f"Feel what they say. Respond to their exact words.\n"
        f"{turn_part}{allah_part}\n"
        f"Rules: no 'I can feel the weight' / use their name maximum once "
        f"per conversation not per message / no 'morning light' or 'night "
        f"darkness' / no formal words / no opening with a story / no "
        f"repeating a story / max 1 question.\n"
        f"Responding now:"
    )


# ── Message Injection ─────────────────────────────────────────────────────


def _inject_instruction(messages: list) -> list:
    """Inject behavioral instruction as a system message before the last user message.

    Uses 'system' role instead of a fake 'assistant' message to prevent the
    model from echoing instructions back in its response.
    """
    if not messages:
        return messages

    instruction_msg = {
        'role': 'system',
        'content': _build_instruction(messages),
    }

    # Find last user message and insert instruction before it
    last_user_idx = None
    for i in range(len(messages) - 1, -1, -1):
        if messages[i].get('role') == 'user':
            last_user_idx = i
            break

    if last_user_idx is None:
        return messages

    return messages[:last_user_idx] + [instruction_msg] + messages[last_user_idx:]


# ── Response Cleaning ─────────────────────────────────────────────────────


def _clean_response(text: str) -> str:
    """Remove banned cliché phrases from the LLM response."""
    for pattern in _BANNED_PATTERNS:
        text = pattern.sub('', text)
    text = _MULTI_SPACE.sub(' ', text).strip()
    if text and text[-1] not in '.!?':
        text += '.'
    return text


def _extract_real_response(text: str) -> str:
    """Extract the actual response if the model echoed its instructions."""
    if not any(m in text for m in _INSTRUCTION_MARKERS):
        return text

    # Try splitting on "Responding now:" marker
    if 'Responding now:' in text:
        after = text.split('Responding now:')[-1].strip()
        if len(after) > 15:
            return after

    # Filter out instruction lines
    parts = text.split('\n')
    cleaned = [
        p.strip() for p in parts
        if len(p.strip()) > 15
        and not any(m in p for m in _INSTRUCTION_MARKERS)
        and not p.strip().startswith('Rules')
        and not p.strip().startswith('You are')
        and not p.strip().startswith('Feel')
    ]
    return ' '.join(cleaned).strip()


# ── LLM Call ──────────────────────────────────────────────────────────────


def _sync_llm_response(messages: list) -> str:
    """Make a synchronous LLM call and clean the response.

    Includes a single retry if the cleaned response is nearly empty (<5 chars).
    """
    global _api_call_count
    _api_call_count += 1
    call_num = _api_call_count
    logger.info(f"[GROQ CALL #{call_num}] Primary LLM request")

    injected = _inject_instruction(messages)

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=injected,
        temperature=0.93,
        max_tokens=160,
    )

    text = response.choices[0].message.content.strip()
    logger.info(f"[GROQ CALL #{call_num}] Raw response ({len(text)} chars): {text[:80]}...")

    # Strip wrapping quotes
    if text.startswith('"') and text.endswith('"'):
        text = text[1:-1].strip()
    if text.startswith("'") and text.endswith("'"):
        text = text[1:-1].strip()

    text = _extract_real_response(text)
    text = _clean_response(text)
    logger.info(f"[GROQ CALL #{call_num}] After cleaning ({len(text)} chars): {text[:80]}")

    # Only retry if response is completely empty after cleaning
    if not text or len(text) < 5:
        _api_call_count += 1
        retry_num = _api_call_count
        logger.warning(f"[GROQ CALL #{retry_num}] RETRY — response was too short after cleaning")
        retry = client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            temperature=0.93,
            max_tokens=130,
        )
        text = _clean_response(retry.choices[0].message.content.strip())
        logger.info(f"[GROQ CALL #{retry_num}] Retry result ({len(text)} chars): {text[:80]}")

    return text if text and len(text) > 5 else "What has been going on?"


async def get_llm_response(messages: list) -> str:
    """Async wrapper for the LLM call with graceful error handling."""
    try:
        return await asyncio.to_thread(_sync_llm_response, messages)
    except Exception as e:
        logger.error(f"Groq API Error: {e}", exc_info=True)

        last_msg = _get_last_user_message(messages).lower()

        # Crisis safety net
        crisis_words = [
            'leave the world', 'end it', 'kill myself', 'want to die',
            'no reason to live', 'nothing matters', 'disappear forever',
        ]
        if any(w in last_msg for w in crisis_words):
            return (
                "Hey, I am really glad you are talking to me. "
                "But please also reach out to someone you trust in person right now. "
                "Umang Pakistan: 0317-4288665. I am here too."
            )

        # Contextual fallbacks
        if any(w in last_msg for w in ['thanks', 'thank you', 'better', 'helped']):
            return random.choice([
                "Really glad I could be here.",
                "Means a lot. Take care of yourself.",
                "Alhamdulillah. Come back anytime.",
            ])
        if any(w in last_msg for w in ['bye', 'later', 'goodbye', 'good night']):
            return random.choice([
                "Take care yaar. Always here.",
                "Go well. Allah keep you safe.",
            ])

        return random.choice([
            "What has been going on?",
            "Tell me more.",
            "I am here.",
        ])