from contextlib import asynccontextmanager
from pathlib import Path

import fitz  # PyMuPDF
import joblib
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

MODELS_DIR = Path(__file__).parent / "models"
VECTORIZER_PATH = MODELS_DIR / "tfidf_vectorizer.joblib"
CLASSIFIER_PATH = MODELS_DIR / "resume_classifier.joblib"


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load the fitted model artifacts once at startup, not per request.
    if VECTORIZER_PATH.exists() and CLASSIFIER_PATH.exists():
        app.state.vectorizer = joblib.load(VECTORIZER_PATH)
        app.state.classifier = joblib.load(CLASSIFIER_PATH)
        print("Loaded tfidf_vectorizer.joblib and resume_classifier.joblib")
    else:
        app.state.vectorizer = None
        app.state.classifier = None
        print(
            "WARNING: models/tfidf_vectorizer.joblib and models/resume_classifier.joblib "
            "not found. Upload endpoint will return text only."
        )
    yield


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    print(f"Received PDF: {file.filename}")

    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="File must be a PDF.")

    try:
        data = await file.read()
        doc = fitz.open(stream=data, filetype="pdf")
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid or corrupted PDF file.")

    pages = []
    for page in doc:
        pages.append(page.get_text())
    doc.close()

    text = "\n\n".join(pages).strip()
    if not text:
        raise HTTPException(status_code=422, detail="No extractable text found in the PDF.")

    if app.state.vectorizer is None or app.state.classifier is None:
        raise HTTPException(
            status_code=503,
            detail="Classification model is not available on the server.",
        )

    try:
        features = app.state.vectorizer.transform([text])
        category = app.state.classifier.predict(features)[0]
    except Exception:
        raise HTTPException(status_code=500, detail="Prediction failed.")

    return {"filename": file.filename, "text": text, "category": str(category)}
