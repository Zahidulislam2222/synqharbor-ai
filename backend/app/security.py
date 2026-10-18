"""Opaque sessions, synchronizer CSRF and bounded request bodies."""
import hashlib
import hmac
import secrets

from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Message, Receive, Scope, Send


def token() -> str:
    return secrets.token_urlsafe(32)


def token_hash(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def csrf_token(secret: str, session: str) -> str:
    return hmac.new(secret.encode(), session.encode(), hashlib.sha256).hexdigest()


class BodyLimit:
    def __init__(self, app: ASGIApp, maximum: int) -> None:
        self.app, self.maximum = app, maximum

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        data = bytearray()
        while True:
            event = await receive()
            if event["type"] == "http.disconnect":
                return
            data.extend(event.get("body", b""))
            if len(data) > self.maximum:
                await JSONResponse({"detail": {"code": "body_limit"}}, status_code=413)(scope, receive, send)
                return
            if not event.get("more_body", False):
                break
        replayed = False

        async def replay() -> Message:
            nonlocal replayed
            if not replayed:
                replayed = True
                return {"type": "http.request", "body": bytes(data), "more_body": False}
            return await receive()

        await self.app(scope, replay, send)
