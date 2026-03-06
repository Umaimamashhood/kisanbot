"""
app.py — KisanBot REST API (production ready)
Run locally:  python app.py
"""

import io
import os
from dotenv import load_dotenv

load_dotenv()

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS

import pdf_loader
import voice_assistant as va

pdf_loader.load_all()

app = Flask(__name__)
CORS(app, origins="*")

# ── Health ────────────────────────────────────────────────────

@app.get("/")
@app.get("/health")
def health():
    return jsonify(
        status="ok",
        version="1.0",
        model=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
        chunks_loaded=len(pdf_loader._chunks),
        supported_languages=["en", "ur"],
    )

# ── Text question ─────────────────────────────────────────────

@app.post("/ask")
def ask():
    data     = request.get_json(silent=True) or {}
    question = (data.get("question") or "").strip()
    if not question:
        return jsonify(error="'question' is required"), 400

    language   = data.get("language") or va.detect_language(question)
    want_audio = bool(data.get("audio", False))
    text       = va.answer(question, language)

    if want_audio:
        mp3 = va.text_to_speech(text, language)
        return send_file(io.BytesIO(mp3), mimetype="audio/mpeg",
                         as_attachment=False, download_name="answer.mp3")

    return jsonify(answer=text, language=language)

# ── Voice question ────────────────────────────────────────────

@app.post("/ask-voice")
def ask_voice():
    if "audio" not in request.files:
        return jsonify(error="'audio' file is required"), 400

    language  = request.form.get("language", "en")
    raw_audio = request.files["audio"].read()

    transcription = va.speech_to_text(raw_audio, language)
    if not transcription:
        return jsonify(error="Could not understand audio, please try again."), 422

    text = va.answer(transcription, language)
    return jsonify(transcription=transcription, answer=text, language=language)

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
    app.run(host="0.0.0.0", port=port, debug=False)
