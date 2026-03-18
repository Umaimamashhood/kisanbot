"""
app.py — KisanBot REST API
Features: Memory per user, Google Drive PDF sync, Bilingual voice
Run: python app.py
UI:  http://127.0.0.1:5000/ui
"""

import io
import os
from dotenv import load_dotenv

load_dotenv()

from flask import Flask, request, jsonify, send_file, render_template
from flask_cors import CORS

import pdf_loader
import voice_assistant as va
import memory

# Try to sync from Google Drive at startup (won't fail if not configured)
try:
    import drive_loader
    drive_loader.sync_drive_pdfs()
except Exception as e:
    print(f"[app] Drive sync skipped: {e}")

pdf_loader.load_all()

app = Flask(__name__, template_folder="templates")
CORS(app, origins="*", supports_credentials=True)

# ── UI ────────────────────────────────────────────────────────

@app.get("/")
@app.get("/ui")
def ui():
    return render_template("kisanbot_ui.html")

# ── Health ────────────────────────────────────────────────────

@app.get("/health")
def health():
    return jsonify(
        status="ok",
        version="2.0",
        model=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
        chunks_loaded=len(pdf_loader._chunks),
        supported_languages=["en", "ur"],
        features=["memory", "google_drive", "voice", "bilingual"]
    )

# ── Text question ─────────────────────────────────────────────

@app.post("/ask")
def ask():
    """
    Body (JSON):
      question  str   — question in English or Urdu
      language  str   — 'en' | 'ur' (auto-detected if omitted)
      audio     bool  — true to receive MP3 back
      user_id   str   — user ID from integrated app (optional, default: anonymous)
    """
    data     = request.get_json(silent=True) or {}
    question = (data.get("question") or "").strip()
    if not question:
        return jsonify(error="'question' is required"), 400

    language   = data.get("language") or va.detect_language(question)
    want_audio = bool(data.get("audio", False))
    user_id    = data.get("user_id", "anonymous")

    text = va.answer(question, language, user_id)

    if want_audio:
        mp3 = va.text_to_speech(text, language)
        return send_file(io.BytesIO(mp3), mimetype="audio/mpeg",
                         as_attachment=False, download_name="answer.mp3")

    return jsonify(answer=text, language=language, user_id=user_id)

# ── Voice question ────────────────────────────────────────────

@app.post("/ask-voice")
def ask_voice():
    """
    Form data:
      audio    file — audio file (WebM, WAV, MP3)
      language str  — 'en' | 'ur'
      user_id  str  — user ID from integrated app
    """
    if "audio" not in request.files:
        return jsonify(error="'audio' file is required"), 400

    language  = request.form.get("language", "en")
    user_id   = request.form.get("user_id", "anonymous")
    raw_audio = request.files["audio"].read()

    transcription = va.speech_to_text(raw_audio, language)
    if not transcription:
        return jsonify(error="Could not understand audio, please try again."), 422

    text = va.answer(transcription, language, user_id)
    return jsonify(transcription=transcription, answer=text,
                   language=language, user_id=user_id)

# ── Memory endpoints ──────────────────────────────────────────

@app.get("/history/<user_id>")
def get_history(user_id):
    """Get full conversation history for a user."""
    hist = memory.get_history(user_id)
    return jsonify(user_id=user_id, history=hist, total=len(hist))

@app.delete("/history/<user_id>")
def clear_history(user_id):
    """Clear all conversation history for a user."""
    memory.clear_history(user_id)
    return jsonify(message=f"History cleared for user '{user_id}'")

# ── Drive sync ────────────────────────────────────────────────

@app.post("/sync-drive")
def sync_drive():
    """Manually trigger Google Drive PDF sync."""
    try:
        import drive_loader
        drive_loader.sync_drive_pdfs()
        return jsonify(
            message="Drive sync complete",
            chunks_loaded=len(pdf_loader._chunks)
        )
    except Exception as e:
        return jsonify(error=str(e)), 500

# ── Upload PDF ────────────────────────────────────────────────

@app.post("/upload-pdf")
def upload_pdf():
    if "pdf" not in request.files:
        return jsonify(error="'pdf' file is required"), 400

    f = request.files["pdf"]
    if not f.filename.lower().endswith(".pdf"):
        return jsonify(error="Only .pdf files are accepted"), 400

    save_path = pdf_loader.DATA_DIR / f.filename
    f.save(save_path)
    pdf_loader._ingest(save_path)
    return jsonify(message=f"'{f.filename}' added to knowledge base.")

# ── run ───────────────────────────────────────────────────────

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)