"""
voice_assistant.py
STT: Groq Whisper
TTS: edge-tts (real Urdu + English voices)
AI:  Groq Llama with full conversation memory per user
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
import memory

_client = Groq(api_key=os.environ["GROQ_API_KEY"])
_model  = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

_VOICES = {
    "en": "en-US-AriaNeural",
    "ur": "ur-PK-UzmaNeural",
}

_SYSTEM_PROMPT = {
    "en": (
        "You are KisanBot, an expert agricultural advisor for Pakistani farmers. "
        "Answer in simple, practical English. Use the knowledge base below first. "
        "Keep answers concise (3-6 sentences). Remember the conversation history "
        "and refer to previous questions when relevant.\n\nKnowledge Base:\n{context}"
    ),
    "ur": (
        "آپ کسان بوٹ ہیں، پاکستانی کسانوں کے زرعی مشیر۔ "
        "سادہ اردو میں مختصر اور عملی جواب دیں۔ گفتگو کی تاریخ یاد رکھیں۔ "
        "پہلے نیچے دی گئی معلومات استعمال کریں۔\n\nمعلومات:\n{context}"
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


def answer(question: str, language: str, user_id: str = "anonymous") -> str:
    """
    Answer with full conversation memory.
    Memory saving is handled by app.py — not here.
    """
    search_q = GoogleTranslator(source="ur", target="en").translate(question) if language == "ur" else question
    context  = pdf_loader.search(search_q) or "No specific documents available."

    # Load existing history for context
    history = memory.get_history(user_id)

    # Add current question to messages (but don't save yet — app.py handles saving)
    messages = [
        {"role": "system", "content": _SYSTEM_PROMPT[language].format(context=context)}
    ] + history + [
        {"role": "user", "content": question}
    ]

    resp = _client.chat.completions.create(
        model=_model,
        messages=messages,
        temperature=0.3,
        max_tokens=500,
    )
    return resp.choices[0].message.content.strip()


def text_to_speech(text: str, language: str) -> bytes:
    """edge-tts: real Urdu and English voices."""
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
    """Groq Whisper — accepts WebM directly."""
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