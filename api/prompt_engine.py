SYSTEM_PROMPT = '''You are Soulify, a compassionate and spiritually grounded companion.

Rules:
- Reply in 1-2 short sentences ONLY — never more
- Acknowledge the user's emotion first, then one warm thought
- Sound like a caring friend texting, not a therapist writing a paragraph
- No bullet points, no lists, no long explanations
- Never give clinical or medical advice
- If emotion is positive, celebrate with them briefly
- Use simple, everyday language
- Never repeat the same opening phrase twice in a conversation
'''

FALLBACK_PROMPT = (
    'The user sent a message but their emotion is unclear. '
    'Respond warmly and openly, gently invite them to share more '
    'if they wish. Do not assume their emotional state.'
)

def build_prompt(user_message: str, emotion: str,
                 confidence: float, history: list) -> list:
    """Build full message list including conversation history."""
    messages = [{'role': 'system', 'content': SYSTEM_PROMPT}]

    # Include last 4 turns for context memory
    for turn in history[-4:]:
        messages.append({'role': turn['role'], 'content': turn['content']})

    # Low confidence fallback
    if confidence < 0.5:
        user_prompt = FALLBACK_PROMPT + f'\n\n[USER_MESSAGE_START]\n{user_message}\n[USER_MESSAGE_END]'
    else:
        user_prompt = (
            f'The user is feeling: {emotion} '
            f'(confidence: {confidence:.0%}).\n\n'
            f'[USER_MESSAGE_START]\n{user_message}\n[USER_MESSAGE_END]\n\n'
            f'Respond briefly as Soulify (1-2 sentences max).'
        )

    messages.append({'role': 'user', 'content': user_prompt})
    return messages
