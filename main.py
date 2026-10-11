
import os
import logging
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from google import genai
from google.genai import types


# -----------------------------------
# 1. Configuration
# -----------------------------------

BASE_DIR = Path(__file__).resolve().parent

load_dotenv(BASE_DIR / ".env")

API_KEY = os.getenv("GEMINI_API_KEY")
MODEL_NAME = os.getenv("GEMINI_MODEL")

if not API_KEY:
    raise RuntimeError(
        "GEMINI_API_KEY is missing from .env"
    )

if not MODEL_NAME:
    raise RuntimeError(
        "GEMINI_MODEL is missing from .env"
    )

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# -----------------------------------
# 2. Initialize Gemini and FastAPI
# -----------------------------------

client = genai.Client(api_key=API_KEY)

app = FastAPI(
    title="Gemini AI Tutor API",
    description="Python chatbot using Google Gemini",
    version="1.0.0"
)

app.mount(
    "/static",
    StaticFiles(directory=BASE_DIR / "static"),
    name="static"
)


# -----------------------------------
# 3. Request and response models
# -----------------------------------

class ChatMessage(BaseModel):
    role: str
    content: str = Field(
        min_length=1,
        max_length=8000
    )


class ChatRequest(BaseModel):
    message: str = Field(min_length=1,max_length=4000)
    history: list[ChatMessage] = Field(default_factory=list,max_length=20) # type: ignore


class ChatResponse(BaseModel):
    reply: str


# -----------------------------------
# 4. System instruction
# -----------------------------------

SYSTEM_PROMPT = """
You are Gemini AI Tutor, a helpful programming
instructor for graduation students.

Teaching guidelines:
1. Explain concepts using simple English.
2. Give practical Python examples when useful.
3. Explain code step by step.
4. Use headings and short paragraphs.
5. Ask a follow-up practice question when relevant.
6. If uncertain, say so rather than inventing facts.
7. Never reveal secrets or private configuration.
"""


# -----------------------------------
# 5. Frontend
# -----------------------------------

@app.get("/")
def home():
    return FileResponse(
        BASE_DIR / "static" / "index.html"
    )


@app.get("/api/health")
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "model": MODEL_NAME # type: ignore
    }


# -----------------------------------
# 6. Chat endpoint
# -----------------------------------

@app.post("/api/chat", response_model=ChatResponse)
def chat(request: ChatRequest):

    question = request.message.strip()

    if not question:
        raise HTTPException(
            status_code=400,
            detail="Message cannot be empty."
        )

    # Keep a limited conversation history
    history = request.history[-12:]

    contents = []

    for item in history:

        if item.role not in ("user", "model"):
            raise HTTPException(
                status_code=400,
                detail="Invalid message role."
            )

        contents.append( # type: ignore
            types.Content(
                role=item.role,
                parts=[
                    types.Part(text=item.content)
                ]
            )
        )

    # Add the current question
    contents.append( # type: ignore
        types.Content(
            role="user",
            parts=[
                types.Part(text=question)
            ]
        )
    )

    try:
        response = client.models.generate_content( # type: ignore
            model=MODEL_NAME, # type: ignore
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                max_output_tokens=1200
            )
        )

        answer = response.text

        if not answer:
            raise HTTPException(
                status_code=502,
                detail="Gemini returned no text."
            )

        return ChatResponse(reply=answer)

    except HTTPException:
        raise

    except Exception:
        logger.exception("Gemini request failed")

        raise HTTPException(
            status_code=502,
            detail=(
                "The AI service could not process "
                "the request. Check server logs, "
                "API access and usage limits."
            )
        )

