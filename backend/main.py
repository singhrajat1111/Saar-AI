from dotenv import load_dotenv
load_dotenv()

import os

from fastapi import FastAPI

from fastapi.middleware.cors import CORSMiddleware



def _cors_origins() -> list[str]:
    # Allow local dev + deployed Vercel frontend.
    # Can still be overridden/extended via CORS_ORIGINS env var.
    default_origins = [
        "http://localhost:3000",
        "https://saar-ai-azure.vercel.app",
    ]

    raw_origins = os.getenv("CORS_ORIGINS")
    if raw_origins:
        env_origins = [origin.strip() for origin in raw_origins.split(",") if origin.strip()]
        # de-dupe while preserving order
        seen = set()
        merged = []
        for o in [*default_origins, *env_origins]:
            if o not in seen:
                seen.add(o)
                merged.append(o)
        return merged

    return default_origins

app = FastAPI(
    title="SAAR AI Backend",
    description="Intelligence Layer for SAAR AI Platform",
    version="1.1.0",
)

# Set up CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "saar_ai_backend"}

from app.api.endpoints import router as api_router
app.include_router(api_router, prefix="/api")
