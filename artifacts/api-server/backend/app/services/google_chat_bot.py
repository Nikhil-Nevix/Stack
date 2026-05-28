"""
Google Chat Bot webhook handler.
Receives events from Google Chat and routes them to the AI chat engine.
"""
import hashlib
import hmac
import json
from fastapi import Request, HTTPException
from ..core.config import settings
from ..utils.logger import logger


async def verify_google_chat_webhook(request: Request) -> dict:
    body = await request.json()
    logger.info(f"Google Chat event: {body.get('type')}")
    return body


def build_google_chat_response(text: str, options: list = None) -> dict:
    """Build a Google Chat response card."""
    if options:
        buttons = [{
            "text": opt,
            "onClick": {"action": {"actionMethodName": "option_selected", "parameters": [{"key": "selection", "value": opt}]}}
        } for opt in options[:5]]
        return {
            "cards": [{
                "sections": [{
                    "widgets": [
                        {"textParagraph": {"text": text}},
                        {"buttons": buttons}
                    ]
                }]
            }]
        }
    return {"text": text}
