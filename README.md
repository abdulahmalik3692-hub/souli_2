# 🌌 Soulify — AI-Powered Emotional Wellness Engine

Soulify is a sophisticated emotional intelligence engine designed to provide therapeutic companionship through deep-learning-driven emotion detection, behavioral analysis, and color psychology.

## 🧠 System Architecture

The project is built as a hybrid intelligence system that combines traditional NLP, behavioral biometrics, and Large Language Models (LLMs).

### 1. Core Intelligence Layer (`model/`)
*   **Emotion Classifier:** Utilizes a `RoBERTa-base` model trained on the `GoEmotions` dataset to identify 28 distinct emotional labels with high precision.
*   **Keyword Boosting:** A heuristic layer that ensures critical emotional triggers are never missed by the neural network.
*   **Sarcasm & Masking Detection:** Advanced regex patterns designed to catch "hidden" distress (e.g., catching when a user says "I'm fine" while exhibiting sad patterns).

### 2. Behavioral Analysis Engine (`behavior.py`)
*   **Typing Biometrics:** Analyzes the user's typing speed (Characters Per Second) to detect contradictions between words and state. 
    *   *Example:* Slow typing paired with positive words triggers a "masking" suspicion, shifting the model's confidence toward hidden distress.

### 3. Color Psychology Engine (`emotion_colors.py`)
*   **Healing Logic:** For negative emotions (Sadness, Anger, Fear), the system dynamically generates "Healing Colors" (e.g., Sunshine Gold for serotonin stimulation) to provide immediate visual relief.
*   **Amplifying Logic:** For positive emotions, the system uses "Amplifying Colors" (e.g., Solar Orange) to sustain and deepen the user's positive state.

### 4. Backend Orchestration (`api/`)
*   **FastAPI Framework:** A high-performance, asynchronous API that manages the flow from message input to therapeutic output.
*   **Groq LLM Integration:** Uses the Llama-3-70B model (via Groq) for ultra-low latency response generation.
*   **Quote Manager:** An intelligent service that triggers context-aware therapeutic quotes and exercises based on emotional intensity and frequency.

### 5. Persistent Memory (`database/`)
*   **MongoDB (Motor):** Asynchronously logs emotional trends and quote history. This allows the system to provide "Long-Term Memory" and avoid repeating the same advice or quotes.

## 🚀 Getting Started

### Prerequisites
* Python 3.10+
* MongoDB Atlas Account
* Groq API Key

### Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/abdulahmalik3692-hub/Soulify-model.git
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Set up your `.env` file:
   ```env
   GROQ_API_KEY=your_key_here
   MONGODB_URI=your_mongodb_uri
   DB_NAME=soulify_db
   ```

### Running the API
```bash
python api/main.py
```

## 🛠 Features
*   **Real-time Emotion Tracking:** Visualized via dynamic UI themes.
*   **Therapeutic Quotes:** Triggered by high-confidence negative emotional states.
*   **Contextual Memory:** The AI remembers your emotional state across messages.
*   **Privacy-First:** Mood logs are stored with message previews only.

---
*Created with ❤️ by the Soulify Team*
