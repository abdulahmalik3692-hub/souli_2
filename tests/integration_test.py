import sys
import asyncio
import os

# Ensure the root directory is on the path
sys.path.insert(0, '.')

from model.emotion_classifier import detect_emotion
from model.behavior import apply_typing_modifier
from api.prompt_engine import build_prompt
from api.quote_manager import should_send_quote

async def run_integration_test():
    print("=" * 65)
    print("   SOULIFY BACKEND INTEGRATION & LOGIC TEST")
    print("=" * 65)
    print()

    # Test 1: Single turn emotion detection and prompt building
    print("🧪 Test 1: Checking emotion classification & prompt building...")
    message = "I want to kill someone"
    session_id = "test_session_1"
    
    er = detect_emotion(message, session_id)
    emotion = er['emotion']
    confidence = apply_typing_modifier(emotion, er['confidence'], 5.0)
    
    print(f"   Input: '{message}'")
    print(f"   Detected Emotion: {emotion.upper()} (Confidence: {confidence:.2%})")
    
    history = []
    messages = build_prompt(message, emotion, confidence, history)
    
    assert messages[0]['role'] == 'system'
    assert len(messages) == 2
    print("   ✅ Test 1 Passed: Prompt structured correctly.")
    print()

    # Test 2: Quote trigger after 3 consecutive matching emotions
    print("🧪 Test 2: Verifying Quote Trigger Logic (3 Consecutive Turns)...")
    history = []
    emotion = "sadness"
    confidence = 0.85
    
    # 1st sad message
    print("   Turn 1 (sadness): Checking if quote triggers...")
    assert not should_send_quote(emotion, confidence, history)
    print("   ✅ Turn 1: Correctly did not trigger quote.")
    history.append({'role': 'user', 'content': "I feel so down today", 'emotion': "sadness"})
    history.append({'role': 'assistant', 'content': "I'm so sorry you feel that way...", 'had_quote': False})

    # 2nd sad message
    print("   Turn 2 (sadness): Checking if quote triggers...")
    assert not should_send_quote(emotion, confidence, history)
    print("   ✅ Turn 2: Correctly did not trigger quote.")
    history.append({'role': 'user', 'content': "Nothing is going right", 'emotion': "sadness"})
    history.append({'role': 'assistant', 'content': "I'm here with you through this...", 'had_quote': False})

    # 3rd sad message
    print("   Turn 3 (sadness): Checking if quote triggers...")
    # Now we have 2 sad user turns in history and the 3rd current emotion is sad
    assert should_send_quote(emotion, confidence, history)
    print("   ✅ Turn 3: Correctly triggered quote!")
    print()

    # Test 3: Emotion change resets quote tracking
    print("🧪 Test 3: Verifying Emotion Change resets Quote Trigger...")
    history = []
    
    # User is sad, then happy, then sad
    history.append({'role': 'user', 'content': "I feel so down today", 'emotion': "sadness"})
    history.append({'role': 'assistant', 'content': "I'm so sorry...", 'had_quote': False})
    
    # Next message is happy
    history.append({'role': 'user', 'content': "Actually I feel great now!", 'emotion': "joy"})
    history.append({'role': 'assistant', 'content': "That's wonderful!", 'had_quote': False})
    
    # Next is sad again
    print("   Current emotion: sadness (preceded by joy, sadness). Checking if quote triggers...")
    assert not should_send_quote("sadness", 0.85, history)
    print("   ✅ Reset: Correctly did not trigger quote (consecutive count was broken by joy).")
    print()

    print("=" * 65)
    print("🎉 ALL INTEGRATION TESTS PASSED SUCCESSFULLY!")
    print("=" * 65)

if __name__ == '__main__':
    asyncio.run(run_integration_test())
