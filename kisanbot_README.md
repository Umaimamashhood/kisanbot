# 🌾 KisanBot v2 — Bilingual Farming Voice Assistant API

> A free, AI-powered REST API for Pakistani farmers. Supports **English and Urdu**, answers farming questions from PDFs stored on **Google Drive** using **FAISS vector search**, remembers **full conversation history** per user, and responds in **spoken audio**.

---

## 📌 Project Summary

KisanBot is a voice-based question-answering system designed for farmers in Pakistan. It is built as a **REST API** that can be integrated into any mobile app, website, or platform. Users from the integrated app send their `user_id` with each request, and KisanBot remembers their full conversation history.

PDFs are stored on **Google Drive** — when the server starts, it automatically downloads all PDFs from the Drive folder and loads them into the knowledge base. Images inside PDFs are automatically ignored — only text is extracted.

---

## 🚀 What's New in v2

| Feature | v1 | v2 |
|---------|----|----|
| User memory per user | ❌ | ✅ Full history in SQLite |
| Google Drive PDF sync | ❌ | ✅ Auto sync at startup |
| Images in PDFs | ❌ | ✅ Auto ignored |
| Strict language replies | ❌ | ✅ No mixing English/Urdu |
| Duplicate memory fix | ❌ | ✅ Saves only once per question |
| FAISS vector search | ✅ | ✅ With keyword fallback |
| Bilingual voice | ✅ | ✅ |

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
| Conversation Memory | SQLite (local database) |
| Translation | deep-translator |
| Language Detection | langdetect |
| PDF Storage | Google Drive |
| Backend | Flask |

---

## 🔌 API Endpoints

### `GET /health` — Server status
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
  "answer": "The best time to sow wheat in Pakistan is October 15 to November 15...",
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

Response:
{
  "transcription": "When to sow wheat?",
  "answer": "The best time to sow wheat...",
  "language": "en",
  "user_id": "user_123"
}
```

### `GET /history/<user_id>` — Get chat history
```json
{
  "user_id": "user_123",
  "total": 4,
  "history": [
    {"role": "user", "content": "When to sow wheat?"},
    {"role": "assistant", "content": "Sow wheat between October 15..."},
    {"role": "user", "content": "What fertilizer should I use?"},
    {"role": "assistant", "content": "Apply DAP at sowing time..."}
  ]
}
```

### `DELETE /history/<user_id>` — Clear chat history
```json
{
  "message": "History cleared for user 'user_123'"
}
```

### `POST /sync-drive` — Sync PDFs from Google Drive
```json
{
  "message": "Drive sync complete",
  "chunks_loaded": 24
}
```

### `POST /upload-pdf` — Upload PDF directly
```
Form data:
  pdf → any farming PDF file
```

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
memory.py    →  saves question + answer to SQLite (once)
            ↓
edge-tts     →  converts answer to speech
            ↓
User hears + sees the answer
```

---

## 🧠 How Memory Works

- Every conversation is saved in `data/memory.db` (SQLite)
- Memory is saved per `user_id` sent by the integrated app
- KisanBot does NOT handle login — the app handles login and sends `user_id`
- Full conversation history is loaded with every request so AI remembers context
- Currently during local testing, all conversations save under `"anonymous"` (default)
- When integrated with real app, each user gets their own separate memory

---

## ☁️ How Google Drive Works

- A Google Cloud Service Account is created with read-only Drive access
- Farming PDFs are uploaded to a specific Google Drive folder
- That folder is shared with the service account email
- At server startup, all PDFs are automatically downloaded to `data/` folder
- FAISS vector search indexes all PDF text for retrieval
- Images in PDFs are automatically ignored — only text extracted
- Add new PDFs to Drive anytime → call `POST /sync-drive` to load them

---

## 🚀 Run Locally

### 1. Clone and install
```bash
git clone https://github.com/Umaimamashhood/kisanbot.git
cd kisanbot
pip install -r requirements.txt
```

### 2. Configure .env
```env
GROQ_API_KEY=your_groq_key_from_console.groq.com
GROQ_MODEL=llama-3.3-70b-versatile
DRIVE_FOLDER_ID=your_google_drive_folder_id
```

### 3. Setup Google Drive (one time)
1. Go to **console.cloud.google.com**
2. Create project → Enable **Google Drive API**
3. Create **Service Account** → download JSON key
4. Rename to `service_account.json` → place in kisanbot folder
5. Share your Drive folder with the service account email
6. Copy folder ID from Drive URL → paste in `.env`

### 4. Run
```bash
python app.py
```

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

---

## 🌍 Language Support

| Feature | English | Urdu |
|---------|---------|------|
| Type question | ✅ | ✅ |
| Speak question | ✅ | ✅ |
| AI answer (strict language) | ✅ English only | ✅ Urdu only |
| Spoken reply | ✅ en-US-AriaNeural | ✅ ur-PK-UzmaNeural |
| PDF text extraction | ✅ | ✅ |
| Auto language detect | ✅ | ✅ |

---

## ⚠️ Security Notes

- **Never upload** `service_account.json` or `.env` to GitHub
- Both are in `.gitignore` for protection
- Real API keys stay on your local machine only

---

*Built with ❤️ for Pakistani farmers. Powered entirely by free AI tools.*
