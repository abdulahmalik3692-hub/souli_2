import sys
sys.path.insert(0, '.')
from model.emotion_classifier import classifier

test_inputs = [
    "I truly admire how hard you work every single day",
    "I adore everything about this person they are perfect",
    "This painting is so beautiful it takes my breath away",
    "That was the funniest thing I have ever seen in my life",
    "I am so angry right now I want to scream",
    "I feel so anxious and nervous I cannot calm down",
    "I am completely in awe of how vast the universe is",
    "That situation was so awkward I wanted to disappear",
    "I am so bored I have nothing to do at all",
    "I feel completely calm and peaceful right now",
    "I have no idea what is going on I am so confused",
    "I really want some food right now I am craving it badly",
    "That is absolutely disgusting I cannot believe it",
    "Seeing others suffer makes my heart ache so deeply",
    "I am completely mesmerized and lost in this moment",
    "I am so excited I cannot wait for tomorrow to come",
    "I am terrified and scared of what might happen next",
    "That was the most horrifying thing I have ever witnessed",
    "I am really curious and interested in learning more about this",
    "I feel so happy and joyful everything is wonderful",
    "I miss the old days everything was so much simpler then",
    "I am so relieved that everything worked out in the end",
    "I feel so deeply in love everything feels magical",
    "I feel so sad and empty I have been crying all day",
    "I feel so satisfied and proud of what I accomplished today",
    "I feel a deep physical attraction and desire",
    "I cannot believe that just happened I am completely shocked",
]

print("=" * 65)
print("   SOULIFY — BLIND EMOTION PREDICTION TEST")
print("=" * 65)
print()

for i, text in enumerate(test_inputs, 1):
    result     = classifier(text[:512])[0]
    predicted  = result['label']
    confidence = result['score']
    print(f"#{i:02d} Predicted : {predicted.upper()}")
    print(f"     Confidence: {confidence:.3f}")
    print(f"     Input     : {text[:60]}")
    print()

print("=" * 65)
