# 🌾 KisanBot — Bilingual Farming Voice Assistant API

A free, production-ready AI voice assistant for Pakistani farmers.
Answers farming questions in **English and Urdu** using a PDF knowledge base, spoken aloud.

---

## 📌 Project Summary

KisanBot is a **REST API** that:
- Accepts text or voice questions from farmers
- Searches a PDF knowledge base using **FAISS vector search**
- Generates answers using **Groq Llama 3.3** (free)
- Returns answers as text + **spoken audio (base64 MP3)**
- Supports **English and Urdu** fully

It can be integrated into any mobile app, web app, WhatsApp bot, or any other platform.

---

## 🗂️ Project Structure

```
kisanbot/
├── .env                  ← API keys (never commit this)
├── .gitignore
├── app.py                ← Flask REST API
├── voice_assistant.py    ← STT + TTS + AI answer logic
├── pdf_loader.py         ← PDF parsing + FAISS vector search
├── requirements.txt      ← All dependencies
├── Procfile              ← For Render/Railway deployment
├── templates/
│   └── kisanbot_ui.html  ← Browser voice interface
└── data/
    └── farming_qa.pdf    ← Farming knowledge base
```

---

## ⚙️ Tech Stack

| Layer | Tool | Cost |
|-------|------|------|
| LLM | Groq Llama 3.3 70B | Free |
| Speech to Text | Groq Whisper Large v3 Turbo | Free |
| Text to Speech | edge-tts — Microsoft Neural voices | Free |
| Vector Embeddings | sentence-transformers (runs locally) | Free |
| Vector Search | FAISS (Facebook AI Similarity Search) | Free |
| PDF Parsing | pdfplumber + PyPDF2 | Free |
| Translation | deep-translator (Google) | Free |
| Language Detection | langdetect | Free |
| Web Server | Flask + Gunicorn | Free |

---

## 🚀 Local Setup

### 1. Install dependencies
```bash
pip install flask flask-cors python-dotenv groq pdfplumber PyPDF2 langdetect deep-translator edge-tts faiss-cpu sentence-transformers numpy gunicorn
```

### 2. Configure .env
```env
GROQ_API_KEY=your_groq_api_key_here     # free at console.groq.com
GROQ_MODEL=llama-3.3-70b-versatile
API_KEY=                                 # optional: protects your API
PORT=5000
FLASK_DEBUG=false
```

### 3. Add PDFs to data/ folder
Drop any farming PDF into `data/`. The included `farming_qa.pdf` covers 50+ Q&As.

### 4. Run
```bash
python app.py
```

### 5. Open UI
```
http://127.0.0.1:5000
```

---

## 🔌 API Reference

### Authentication (optional)
If `API_KEY` is set in `.env`, include this header in every request:
```
X-API-Key: your_api_key_here
```

---

### GET /health
Check server status.
```json
{
  "status": "ok",
  "model": "llama-3.3-70b-versatile",
  "chunks_loaded": 42,
  "auth_enabled": false
}
```

---

### POST /ask — Text question
**Request:**
```json
{
  "question": "When should I sow wheat?",
  "language": "en",
  "audio": true
}
```
**Response:**
```json
{
  "answer": "The best sowing time for wheat is October 15 to November 15...",
  "language": "en",
  "audio_b64": "//NExAA...base64 MP3 data...",
  "audio_mime": "audio/mpeg"
}
```

**Play audio in JavaScript:**
```javascript
const audio = new Audio("data:audio/mpeg;base64," + response.audio_b64);
audio.play();
```

---

### POST /ask-voice — Voice question
**Request (multipart form):**
```
audio    → audio file (WebM/WAV/MP3)
language → "en" or "ur"
audio    → "1" to get audio response
```
**Response:**
```json
{
  "transcription": "When should I sow wheat?",
  "answer": "The best sowing time is October 15 to November 15...",
  "language": "en",
  "audio_b64": "//NExAA...base64 MP3...",
  "audio_mime": "audio/mpeg"
}
```

---

### POST /upload-pdf
Add a new PDF to the live knowledge base.
```
Form data: pdf → PDF file
```
```json
{
  "message": "'guide.pdf' added to knowledge base.",
  "chunks_loaded": 56
}
```

---

## 🧠 How the RAG Pipeline Works

```
User speaks or types
       ↓
[Groq Whisper]        audio → text transcription
       ↓
[langdetect]          detect English or Urdu
       ↓
[deep-translator]     Urdu → English for better search
       ↓
[sentence-transformers]  question → vector embedding
       ↓
[FAISS]               search PDF chunks → top 4 relevant
       ↓
[Groq Llama 3.3]      generate answer from context
       ↓
[edge-tts]            answer text → MP3 audio
       ↓
JSON response: answer text + base64 audio
```

---

## 🌍 Integration Guide

KisanBot returns standard JSON — integrate into anything.

### React / Web App
```javascript
const res = await fetch("https://your-api.onrender.com/ask", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ question: "گندم کب بوئیں؟", language: "ur", audio: true })
});
const data = await res.json();

// Show answer text
console.log(data.answer);

// Play audio
const audio = new Audio("data:audio/mpeg;base64," + data.audio_b64);
audio.play();
```

### Android App (Kotlin)
```kotlin
val body = JSONObject()
body.put("question", "When to sow wheat?")
body.put("language", "en")
body.put("audio", true)

// Parse response
val audioBytes = Base64.decode(response.getString("audio_b64"), Base64.DEFAULT)
// Play with MediaPlayer
```

### WhatsApp Bot
```python
response = requests.post("https://your-api.onrender.com/ask-voice",
    files={"audio": open("voice_note.ogg", "rb")},
    data={"language": "ur"}
)
reply_text = response.json()["answer"]
```

### With API Key
```javascript
headers: {
  "Content-Type": "application/json",
  "X-API-Key": "your_secret_key"
}
```

---

## ☁️ Deployment — Render.com (Free)

### Step 1 — Push to GitHub
```bash
git init
git add .
git commit -m "KisanBot"
git remote add origin https://github.com/yourusername/kisanbot.git
git push -u origin main
```

### Step 2 — Deploy on Render
1. Go to https://render.com → Sign up free
2. New → Web Service → Connect GitHub repo
3. Set:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app --bind 0.0.0.0:$PORT --workers 1 --timeout 120`
4. Add Environment Variables:
   - `GROQ_API_KEY` = your key
   - `GROQ_MODEL` = llama-3.3-70b-versatile
   - `API_KEY` = any secret string you choose
5. Click **Deploy**

Your live API URL:
```
https://kisanbot.onrender.com/health
```

### Alternative — Railway.app
1. Go to https://railway.app → New Project → GitHub repo
2. Add same environment variables
3. Auto-deploys using the `Procfile`

---

## ✅ Integration Checklist

| Feature | Status |
|---------|--------|
| REST API with JSON responses | ✅ |
| Voice input — Speech to Text | ✅ Groq Whisper |
| Voice output — Text to Speech | ✅ edge-tts Urdu + English |
| Bilingual English + Urdu | ✅ |
| PDF knowledge base | ✅ |
| FAISS vector search | ✅ |
| API key authentication | ✅ |
| CORS enabled for any client | ✅ |
| Base64 audio in JSON | ✅ Easy to integrate |
| Production server gunicorn | ✅ |
| Free cloud deployment | ✅ Render / Railway |
| Debug mode off in production | ✅ |

---

## ❓ Troubleshooting

| Problem | Fix |
|---------|-----|
| model decommissioned error | Set `GROQ_MODEL=llama-3.3-70b-versatile` in `.env` |
| Server offline in browser | Go to `http://127.0.0.1:5000` not the HTML file |
| Microphone blocked | Allow mic: `chrome://settings/content/microphone` |
| Urdu not speaking | `pip install edge-tts` |
| Audio not playing in app | Decode base64 and play as `audio/mpeg` |
| 401 Unauthorized | Pass `X-API-Key` header with your key |

---

*Built for Pakistani farmers. All tools are completely free.*
