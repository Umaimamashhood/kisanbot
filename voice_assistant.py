"""
voice_assistant.py
STT: Groq Whisper
TTS: edge-tts (real Urdu + English voices, free)
AI:  Groq Llama
"""

import io
import os
import asyncio
import tempfile

from groq import Groq
import edge_tts
from langdetect import detect, LangDetectException
from deep_translator import GoogleTranslator

import pdf_loader

_client = Groq(api_key=os.environ["GROQ_API_KEY"])
_model  = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

# Real voices for each language
_VOICES = {
    "en": "en-US-AriaNeural",       # clear English female voice
    "ur": "ur-PK-UzmaNeural",       # real Urdu female voice
}

_PROMPT = {
    "en": (
        "You are KisanBot, an expert agricultural advisor for Pakistani farmers. "
        "Answer in simple, practical English. Use the knowledge base below first. "
        "Keep answers concise (3-6 sentences).\n\nKnowledge Base:\n{context}"
    ),
    "ur": (
        "آپ کسان بوٹ ہیں، پاکستانی کسانوں کے زرعی مشیر۔ "
        "سادہ اردو میں مختصر اور عملی جواب دیں۔ پہلے نیچے دی گئی معلومات استعمال کریں۔\n\nمعلومات:\n{context}"
    ),
}


def detect_language(text: str) -> str:
    if sum(1 for c in text if "\u0600" <= c <= "\u06FF") > 2:
        return "ur"
    try:
        lang = detect(text)
        return "ur" if lang in ("ur", "ar", "hi", "fa") else "en"
    except LangDetectException:
        return "en"


def answer(question: str, language: str) -> str:
    search_q = GoogleTranslator(source="ur", target="en").translate(question) if language == "ur" else question
    context  = pdf_loader.search(search_q) or "No specific documents available."

    resp = _client.chat.completions.create(
        model=_model,
        messages=[
            {"role": "system", "content": _PROMPT[language].format(context=context)},
            {"role": "user",   "content": question},
        ],
        temperature=0.3,
        max_tokens=500,
    )
    return resp.choices[0].message.content.strip()


def text_to_speech(text: str, language: str) -> bytes:
    """edge-tts: real Urdu and English voices, returns MP3 bytes."""
    voice = _VOICES.get(language, _VOICES["en"])

    async def _synthesise():
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
            tmp_path = tmp.name
        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(tmp_path)
        with open(tmp_path, "rb") as f:
            data = f.read()
        os.unlink(tmp_path)
        return data

    return asyncio.run(_synthesise())


def speech_to_text(audio_bytes: bytes, language: str) -> str:
    """Groq Whisper — accepts WebM directly, no conversion needed."""
    whisper_lang = "ur" if language == "ur" else "en"

    with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as tmp:
        tmp.write(audio_bytes)
        tmp_path = tmp.name

    try:
        with open(tmp_path, "rb") as f:
            result = _client.audio.transcriptions.create(
                model="whisper-large-v3-turbo",
                file=("question.webm", f, "audio/webm"),
                language=whisper_lang,
            )
        return result.text.strip()
    except Exception as e:
        raise RuntimeError(f"STT failed: {e}") from e
    finally:
        os.unlink(tmp_path)