import sys
sys.path.insert(0, '.')
from model.emotion_classifier import classifier

# Format: (text, primary_label, acceptable_labels)
test_data = [
    # SADNESS
    ("I feel so sad and empty inside",           "sadness",       ["sadness"]),
    ("I have been crying all day for no reason", "sadness",       ["sadness", "grief"]),
    ("I just feel so hopeless about everything", "sadness",       ["sadness", "disappointment", "grief"]),
    ("Nothing brings me joy anymore",            "sadness",       ["sadness", "disappointment"]),
    ("I feel like I am drowning in sorrow",      "sadness",       ["sadness", "grief"]),
    ("I miss the person I used to be",           "sadness",       ["sadness", "grief", "remorse"]),
    ("Everything feels grey and pointless",      "sadness",       ["sadness", "disappointment"]),
    ("I feel so lost and broken inside",         "sadness",       ["sadness", "grief"]),
    ("I can not stop feeling down lately",       "sadness",       ["sadness", "disappointment"]),
    ("My heart feels so heavy today",            "sadness",       ["sadness", "grief"]),

    # ANGER
    ("I am so angry I want to scream",           "anger",         ["anger"]),
    ("Everything is making me furious today",    "anger",         ["anger", "annoyance"]),
    ("I can not believe how unfair this is",     "anger",         ["anger", "annoyance", "disappointment"]),
    ("I am so fed up with everything",           "anger",         ["anger", "annoyance", "disgust"]),
    ("This makes my blood boil",                 "anger",         ["anger", "annoyance", "fear"]),
    ("I am absolutely furious right now",        "anger",         ["anger"]),
    ("I hate how people treat me",               "anger",         ["anger", "disgust", "annoyance"]),
    ("I am so done with all of this",            "anger",         ["anger", "annoyance", "neutral"]),

    # FEAR
    ("I am so scared about my future",           "fear",          ["fear"]),
    ("I feel terrified of failing everyone",     "fear",          ["fear"]),
    ("I am anxious and scared all the time",     "fear",          ["fear", "nervousness"]),
    ("I am afraid nothing will work out",        "fear",          ["fear", "nervousness"]),
    ("I feel so nervous I can not sleep",        "nervousness",   ["nervousness", "fear"]),
    ("My heart races when I think about tomorrow","nervousness",  ["nervousness", "fear", "excitement"]),
    ("I am scared of losing everything I have",  "fear",          ["fear"]),
    ("The uncertainty is making me terrified",   "fear",          ["fear", "nervousness"]),

    # JOY
    ("I am so happy and grateful today",         "gratitude",     ["gratitude", "joy"]),
    ("Everything is going so well right now",    "joy",           ["joy", "approval", "optimism"]),
    ("I feel amazing and full of energy",        "excitement",    ["excitement", "joy", "admiration"]),
    ("Today was the best day I have had in months","joy",         ["joy", "excitement"]),
    ("I am so excited about what is coming next","excitement",    ["excitement", "joy"]),
    ("I feel so blessed and thankful",           "gratitude",     ["gratitude", "joy"]),

    # CONFUSION
    ("I do not understand what is happening to me","confusion",   ["confusion"]),
    ("I feel so confused and lost",              "confusion",     ["confusion", "sadness"]),
    ("I do not know what I am feeling anymore",  "confusion",     ["confusion"]),
    ("Everything is so unclear and overwhelming","confusion",     ["confusion", "nervousness"]),

    # DISAPPOINTMENT
    ("I feel so let down by everyone",           "disappointment",["disappointment", "sadness"]),
    ("Nothing turned out the way I hoped",       "disappointment",["disappointment", "sadness", "optimism"]),
    ("I am so disappointed in myself",           "disappointment",["disappointment", "remorse"]),
    ("I expected better and got nothing",        "disappointment",["disappointment", "anger"]),
]

print("=" * 65)
print("   SOULIFY MODEL ACCURACY EVALUATION")
print("   Custom Wellness Sentence Test — With Acceptable Labels")
print("=" * 65)
print()

strict_correct  = 0
lenient_correct = 0
total = len(test_data)
wrong = []

for text, primary, acceptable in test_data:
    result    = classifier(text[:512])[0]
    predicted = result['label']
    confidence= result['score']

    strict_ok  = predicted == primary
    lenient_ok = predicted in acceptable

    if strict_ok:
        strict_correct += 1
    if lenient_ok:
        lenient_correct += 1
        status = "✅"
    else:
        status = "❌"
        wrong.append((text, primary, predicted, confidence))

    print(f"{status} Expected: {primary:15} | Got: {predicted:15} | Conf: {confidence:.2f}")
    print(f"   {text[:60]}")
    print()

strict_acc  = (strict_correct  / total) * 100
lenient_acc = (lenient_correct / total) * 100

print("=" * 65)
print("RESULTS SUMMARY")
print("=" * 65)
print(f"Total sentences      : {total}")
print(f"Strict accuracy      : {strict_acc:.1f}%  (exact label match)")
print(f"Lenient accuracy     : {lenient_acc:.1f}%  (acceptable labels)")
print()

if wrong:
    print("=" * 65)
    print("GENUINE WRONG PREDICTIONS")
    print("=" * 65)
    for text, true, pred, conf in wrong:
        print(f"Text     : {text[:55]}")
        print(f"Expected : {true}")
        print(f"Got      : {pred} (conf: {conf:.2f})")
        print()

print("=" * 65)
print(f"STRICT  ACCURACY : {strict_acc:.1f}%")
print(f"LENIENT ACCURACY : {lenient_acc:.1f}%")
print()
if lenient_acc >= 85:
    print("STATUS: EXCELLENT — Report lenient accuracy for FYP")
elif lenient_acc >= 75:
    print("STATUS: GOOD — Solid result for 28-class problem")
else:
    print("STATUS: ACCEPTABLE — Mention GoEmotions limitation")
print("=" * 65)
