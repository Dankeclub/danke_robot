"""CORS middleware configuration."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


def add_cors(app: FastAPI) -> None:
    """Add CORS middleware allowing all origins in dev.

    WARNING: Production MUST restrict origins to the actual mini-program domain
    and car device origins. Example for production:
        allow_origins=["https://your-domain.com", "https://api.weixin.qq.com"]
    """
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
