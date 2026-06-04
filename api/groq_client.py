import os
import re
import asyncio
import random
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

_groq_api_key = os.environ.get('GROQ_API_KEY', '')
if not _groq_api_key:
    raise EnvironmentError('GROQ_API_KEY is not set.')

client = Groq(api_key=_groq_api_key)


def _get_last_user_message(messages: list) -> str:
    for m in reversed(messages):
        if m.get('role') == 'user':
            return m.get('content', '')
    return ''


def _get_turn_count(messages: list) -> int:
    return len([m for m in messages if m.get('role') == 'user'])


def _count_used_stories(messages: list) -> int:
    names = [
        'Prophet Ayub', 'Prophet Yusuf', 'Prophet Musa', 'Prophet Muhammad',
        'Prophet Nuh', 'Prophet Ibrahim', 'Prophet Yaqub', 'Prophet Yunus',
        'Nelson Mandela', 'Malala', 'Viktor Frankl', 'Khadijah'
    ]
    used = set()
    for m in messages:
        if m.get('role') == 'assistant':
            for name in names:
                if name in m.get('content', ''):
                    used.add(name)
    return len(used)


def _get_used_names(messages: list) -> str:
    names = [
        'Prophet Ayub', 'Prophet Yusuf', 'Prophet Musa', 'Prophet Muhammad',
        'Prophet Nuh', 'Prophet Ibrahim', 'Prophet Yaqub', 'Prophet Yunus',
        'Nelson Mandela', 'Malala', 'Viktor Frankl', 'Khadijah'
    ]
    used = []
    for m in messages:
        if m.get('role') == 'assistant':
            for name in names:
                if name in m.get('content', '') and name not in used:
                    used.append(name)
    return ', '.join(used) if used else 'none'


def _detect_allah_mention(message: str) -> bool:
    return any(k in message.lower() for k in
               ['allah', 'god', 'rab', 'rabb', 'khuda', 'almighty'])


def _detect_type(message: str) -> str:
    msg = message.lower().strip()
    if any(w in msg for w in ['thanks', 'thank you', 'shukria', 'jazakallah',
                               'feel better', 'helped me', 'feel good now',
                               'you helped', 'appreciate']):
        return 'gratitude'
    if any(w in msg for w in ['bye', 'later', 'goodbye', 'good night',
                               'will talk', 'see you', 'gtg']):
        return 'goodbye'
    if any(w in msg for w in ['shutup', 'shut up', 'go away', 'leave me']):
        return 'pushback'
    if any(w in msg for w in ['never mind', 'forget it', 'leave it',
                               'doesnt matter', "doesn't matter"]):
        return 'deflecting'
    if any(w in msg for w in ['haha', 'lol', 'hehe', 'but fine',
                               'its fine', "it's fine", 'but okay']):
        return 'dark_humor'
    if any(w in msg for w in ['shame on you', 'worst', 'useless',
                               'not helping', 'you failed']):
        return 'criticism'
    return 'normal'



def _build_instruction(messages: list) -> str:
    # Check if shukr was already mentioned in recent responses
    recent_assistant = [
        m.get('content', '') for m in messages[-6:]
        if m.get('role') == 'assistant'
    ]
    shukr_overused = sum(
        1 for m in recent_assistant
        if 'shukr' in m.lower() or 'gratitude' in m.lower() or 'grateful' in m.lower()
    ) >= 2

    # Check if user pushed back on shukr
    shukr_rejected = any(
        'shukr' in m.get('content', '').lower() and
        any(w in m.get('content', '').lower()
            for w in ['stop', 'cant', "can't", 'easy', 'hard', 'how', 'not easy'])
        for m in messages
        if m.get('role') == 'user'
    )
    turn = _get_turn_count(messages)
    last = _get_last_user_message(messages)
    msg = last.lower()
    used = _count_used_stories(messages)
    used_names = _get_used_names(messages)
    allah = _detect_allah_mention(last)
    msg_type = _detect_type(last)

    # Special types
    if msg_type == 'gratitude':
        return "They thanked me. Receive it warmly. 1 sentence. Casual like a friend. No story."
    if msg_type == 'goodbye':
        return "They are leaving. 1 warm casual line. Like 'Take care yaar. Always here.'"
    if msg_type == 'pushback':
        return "They pushed me away. Respect it. 1 short line only."
    if msg_type == 'deflecting':
        return "They pulled back. Hold door open. 1 casual sentence. Like 'Okay, here whenever you want.'"
    if msg_type == 'dark_humor':
        return "They used dark humor. Match the lightness first. Then gently go one layer deeper with one real question."
    if msg_type == 'criticism':
        return "They criticized me. Stay humble and warm. 1 sentence."

    # Story rule
    if used == 0:
        story_rule = "No stories used yet. You can use ONE story from the pool if it genuinely mirrors their exact situation. Save it for a moment that truly calls for it."
    elif used == 1:
        story_rule = f"Story already used: {used_names}. No more stories now. Just be their warm friend."
    else:
        story_rule = f"Stories used: {used_names}. No more stories. Just be present and real."

    # Turn logic
    if turn <= 1:
        turn_part = "Very early. Just listen. Ask one warm casual question. No stories yet."
    elif turn == 2:
        turn_part = "You know a little. Be warm and natural. No story yet."
    else:
        # Check if conversation shows persistent negativity
        negative_count = sum(
            1 for m in messages
            if m.get('role') == 'user'
            and any(w in m.get('content', '').lower()
                    for w in ['cant', "can't", 'nothing', 'why me', 'everyone',
                              'against', 'lonely', 'stuck', 'hopeless'])
        )

        if negative_count >= 1 and used == 0:
            turn_part = (
                f"Turn {turn + 1}. This person has been struggling through multiple messages. "
                f"Now is the right moment to use ONE Prophet story that genuinely mirrors their pain. "
                f"Feel with them first — one sentence. Then bring the story briefly. "
                f"Connect it to their exact situation. {story_rule}"
            )
        else:
            turn_part = (
                f"Turn {turn + 1}. You know them well. Be their closest friend. {story_rule}"
            )

    # Allah
    allah_part = ""
    if allah:
        if used < 1:
            allah_part = "\nALLAH MENTIONED: Sacred moment. Bring His love through one real story. Acknowledge first. Remind them hopelessness is haram and Allah never abandons those who hold on."
        else:
            allah_part = "\nALLAH MENTIONED: No more stories. Bring His love through real warm words. Remind them that a heart still asking has not lost faith. When you take one step toward Allah He comes running."

    return (
        f"You are Souli. Spiritual buddy. WhatsApp friend tone.\n"
        f"Feel what they say. Respond to their exact words.\n"
        f"{turn_part}{allah_part}\n"
        f"Rules: no 'I can feel the weight' / use their name maximum once per conversation not per message / no 'morning light' or 'night darkness' / "
        f"no formal words / no opening with a story / no repeating a story / max 1 question.\n"
        f"Responding now:"
    )


def _inject_instruction(messages: list) -> list:
    if not messages:
        return messages
    last_user_idx = None
    for i in range(len(messages) - 1, -1, -1):
        if messages[i].get('role') == 'user':
            last_user_idx = i
            break
    if last_user_idx is None:
        return messages
    instruction_turn = {
        'role': 'assistant',
        'content': _build_instruction(messages)
    }
    return messages[:last_user_idx] + [instruction_turn] + messages[last_user_idx:]


def _clean_response(text: str) -> str:
    banned = [
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
        r"[Ff]resh start today[^.]*\.\s*",
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
    for pattern in banned:
        text = re.sub(pattern, '', text)
    text = re.sub(r'  +', ' ', text).strip()
    if text and text[-1] not in '.!?':
        text += '.'
    return text


def _extract_real_response(text: str) -> str:
    markers = ['You are Souli', 'Responding now:', 'Rules:', 'ALLAH MENTIONED', 'Feel what']
    if not any(m in text for m in markers):
        return text
    if 'Responding now:' in text:
        after = text.split('Responding now:')[-1].strip()
        if len(after) > 15:
            return after
    parts = text.split('\n')
    cleaned = [
        p.strip() for p in parts
        if len(p.strip()) > 15
        and not any(m in p for m in markers)
        and not p.strip().startswith('Rules')
        and not p.strip().startswith('You are')
        and not p.strip().startswith('Feel')
    ]
    return ' '.join(cleaned).strip()


def _sync_llm_response(messages: list) -> str:
    injected = _inject_instruction(messages)

    response = client.chat.completions.create(
        model='llama-3.3-70b-versatile',
        messages=injected,
        temperature=0.93,
        max_tokens=160,
    )

    text = response.choices[0].message.content.strip()

    if text.startswith('"') and text.endswith('"'):
        text = text[1:-1].strip()
    if text.startswith("'") and text.endswith("'"):
        text = text[1:-1].strip()

    text = _extract_real_response(text)
    text = _clean_response(text)

    if not text or len(text) < 15:
        retry = client.chat.completions.create(
            model='llama-3.3-70b-versatile',
            messages=messages,
            temperature=0.93,
            max_tokens=130,
        )
        text = _clean_response(retry.choices[0].message.content.strip())

    return text if text and len(text) > 10 else "What has been going on?"


async def get_llm_response(messages: list) -> str:
    try:
        return await asyncio.to_thread(_sync_llm_response, messages)
    except Exception as e:
        import traceback
        print(f"Groq API Error: {e}")
        traceback.print_exc()

        last_msg = _get_last_user_message(messages).lower()

        crisis_words = ['leave the world', 'end it', 'kill myself', 'want to die',
                        'no reason to live', 'nothing matters', 'disappear forever']
        if any(w in last_msg for w in crisis_words):
            return (
                "Hey, I am really glad you are talking to me. "
                "But please also reach out to someone you trust in person right now. "
                "Umang Pakistan: 0317-4288665. I am here too."
            )
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