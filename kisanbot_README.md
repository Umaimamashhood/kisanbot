# 🌾 KisanBot — Bilingual Farming Voice Assistant API

A free, AI-powered REST API for Pakistani farmers that supports **English and Urdu**, answers farming questions from PDFs stored on **Google Drive**, remembers **full conversation history** per user, and responds in **spoken audio**.

---

## 📌 Project Summary

KisanBot is a voice-based question-answering system designed for farmers in Pakistan. It is built as a REST API that can be integrated into any mobile app, website, or platform. Users send their `user_id` with each request and KisanBot remembers their full conversation history. PDFs are stored on Google Drive and automatically downloaded at startup. Images inside PDFs are ignored — only text is extracted.

---

## 🗂️ Project Structure

```
kisanbot/
├── .env                    ← API keys and Drive folder ID (not on GitHub)
├── .gitignore              ← protects secrets
├── app.py                  ← Flask REST API (7 endpoints)
├── voice_assistant.py      ← STT, TTS, AI with memory
├── pdf_loader.py           ← PDF text extraction + FAISS search
├── memory.py               ← SQLite conversation history per user
├── drive_loader.py         ← Google Drive PDF sync
├── requirements.txt        ← all dependencies
├── service_account.json    ← Google service account (never upload!)
├── templates/
│   └── kisanbot_ui.html    ← browser UI for testing
└── data/
    ├── .gitkeep            ← keeps folder in git
    ├── memory.db           ← auto-created SQLite database (not on GitHub)
    └── *.pdf               ← PDFs downloaded from Drive (not on GitHub)
```

---

## ⚙️ Tech Stack (All Free)

| Layer | Tool |
|-------|------|
| LLM (AI answers) | Groq — Llama 3.3 70B |
| Speech to Text | Groq Whisper Large v3 Turbo |
| Text to Speech | edge-tts (Microsoft Neural voices) |
| Vector Embeddings | sentence-transformers (local) |
| Vector Search | FAISS (Facebook AI) |
| PDF Text Extraction | pdfplumber + PyPDF2 |
| Conversation Memory | SQLite |
| Translation | deep-translator |
| Language Detection | langdetect |
| PDF Storage | Google Drive |
| Backend | Flask |

---

## 🧠 How It Works

```
User speaks/types question  +  user_id
            ↓
Groq Whisper  →  converts voice to text
            ↓
langdetect   →  detects English or Urdu
            ↓
memory.py    →  loads full conversation history
            ↓
FAISS Search →  finds relevant PDF chunks from Drive
            ↓
Groq Llama   →  generates answer in detected language only
            ↓
memory.py    →  saves question + answer to SQLite
            ↓
edge-tts     →  converts answer to speech
            ↓
User hears + sees the answer
```

---

## 🧠 Conversation Memory

Every conversation is saved in `data/memory.db` (SQLite database) per user. When the integrated app calls the API, it sends the logged-in user's ID with every request. KisanBot loads that user's full past conversation and sends it to the AI so it remembers everything discussed before. After answering, the new question and answer are saved back to the database.

KisanBot does not handle login — the integrated app handles login and just passes the `user_id`. During local testing all conversations save under `"anonymous"` by default.

---

## ☁️ Google Drive Integration

A Google Cloud Service Account is created with read-only access to a specific Google Drive folder. All farming PDFs are uploaded to that folder. When the server starts, it automatically downloads all PDFs into the `data/` folder and indexes them using FAISS vector search. New PDFs can be added to Drive anytime and loaded by calling `POST /sync-drive` without restarting the server.

---

## 🔌 API Endpoints

### `GET /health`
```json
{
  "status": "ok",
  "version": "2.0",
  "model": "llama-3.3-70b-versatile",
  "chunks_loaded": 12,
  "supported_languages": ["en", "ur"],
  "features": ["memory", "google_drive", "voice", "bilingual"]
}
```

### `POST /ask` — Text question
```json
Request:
{
  "question": "When to sow wheat?",
  "language": "en",
  "audio": false,
  "user_id": "user_123"
}
Response:
{
  "answer": "The best time to sow wheat is October 15 to November 15...",
  "language": "en",
  "user_id": "user_123"
}
```
> Set `"audio": true` to receive MP3 spoken answer.

### `POST /ask-voice` — Voice question
```
Form data:
  audio    → audio file (WebM, WAV, MP3)
  language → "en" or "ur"
  user_id  → user ID from integrated app
```

### `GET /history/<user_id>` — Get conversation history
```json
{
  "user_id": "user_123",
  "total": 4,
  "history": [
    {"role": "user", "content": "When to sow wheat?"},
    {"role": "assistant", "content": "Sow wheat between October 15..."}
  ]
}
```

### `DELETE /history/<user_id>` — Clear conversation history

### `POST /sync-drive` — Sync new PDFs from Google Drive

### `POST /upload-pdf` — Upload PDF directly to knowledge base

---

## 🌍 Language Support

| Feature | English | Urdu |
|---------|---------|------|
| Type question | ✅ | ✅ |
| Speak question | ✅ | ✅ |
| AI answer | ✅ English only | ✅ Urdu only |
| Spoken reply | ✅ en-US-AriaNeural | ✅ ur-PK-UzmaNeural |
| PDF text extraction | ✅ | ✅ |
| Auto language detect | ✅ | ✅ |

---

## 🚀 Run Locally

```bash
git clone https://github.com/Umaimamashhood/kisanbot.git
cd kisanbot
pip install -r requirements.txt
python app.py
```

Open browser: `http://127.0.0.1:5000`

---

## 🔧 Integration Example

```javascript
const response = await fetch('http://your-api/ask', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    question: 'When to sow wheat?',
    language: 'en',
    user_id: currentUser.id
  })
});
const data = await response.json();
console.log(data.answer);
```




