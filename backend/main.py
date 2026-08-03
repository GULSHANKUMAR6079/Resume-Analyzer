import logging
import httpx
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.core.config import (
    ALLOWED_ORIGINS,
    APP_DESCRIPTION,
    APP_TITLE,
    APP_VERSION,
    SPACY_MODEL_PRIMARY,
    SPACY_MODEL_SECONDARY,
    SENTENCE_TRANSFORMER_MODEL,
)
from backend.api.routes import router
from backend.database.supabase_db import set_shared_client

logger = logging.getLogger('ats_resume_scorer')
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing Next-Gen ATS Resume Analyzer API...")

    # 1. Initialize persistent pooled Async HTTP Client
    http_client = httpx.AsyncClient(timeout=15.0)
    set_shared_client(http_client)
    app.state.http_client = http_client

    # 2. Load spaCy NLP Model
    import spacy
    logger.info(f"Loading spaCy NLP model: {SPACY_MODEL_PRIMARY}")
    try:
        app.state.nlp = spacy.load(SPACY_MODEL_PRIMARY)
        logger.info(f"Successfully loaded {SPACY_MODEL_PRIMARY}")
    except OSError:
        logger.warning(f"Primary spaCy model {SPACY_MODEL_PRIMARY} not found. Loading fallback: {SPACY_MODEL_SECONDARY}")
        try:
            app.state.nlp = spacy.load(SPACY_MODEL_SECONDARY)
            logger.info(f"Successfully loaded fallback {SPACY_MODEL_SECONDARY}")
        except OSError:
            logger.error("No spaCy model installed. SpaCy NER features will operate in basic mode.")
            app.state.nlp = None

    # 3. Load SentenceTransformer Embedder
    logger.info(f"Loading SentenceTransformer: {SENTENCE_TRANSFORMER_MODEL}")
    from sentence_transformers import SentenceTransformer
    app.state.embedder = SentenceTransformer(SENTENCE_TRANSFORMER_MODEL)
    logger.info(f"Successfully loaded {SENTENCE_TRANSFORMER_MODEL}")

    logger.info("All AI models loaded and ready to serve requests.")
    yield

    logger.info("Shutting down API and closing HTTP connections...")
    await http_client.aclose()

app = FastAPI(
    title=APP_TITLE,
    description=APP_DESCRIPTION,
    version=APP_VERSION,
    lifespan=lifespan,
    docs_url='/docs',
    redoc_url='/redoc'
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

app.include_router(router)

@app.get('/')
async def root():
    return {
        'name': APP_TITLE,
        'version': APP_VERSION,
        'status': 'online',
        'endpoints': {
            'POST /api/v1/analyze-resume': 'Analyze resume document against optional job description',
            'GET /api/v1/history': 'Retrieve user past resume analysis history',
            'DELETE /api/v1/history/:id': 'Delete specific analysis record',
            'POST /api/v1/generate-pdf': 'Compile & download PDF report',
            'GET /api/v1/health': 'Check backend status and loaded AI models',
        }
    }

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(
        'backend.main:app',
        host='0.0.0.0',
        port=8000,
        reload=True
    )
