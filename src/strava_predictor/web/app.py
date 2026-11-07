"""FastAPI application factory: security headers, templates, and routes."""

import time
from collections.abc import Callable
from datetime import date
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.formparsers import MultiPartParser
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from strava_predictor import config
from strava_predictor.web import formatting
from strava_predictor.web.sessions import SessionStore

WEB_DIR = Path(__file__).parent
CSP = "default-src 'self'"
BODY_LIMIT = config.MAX_UPLOAD_BYTES + config.REQUEST_OVERHEAD_BYTES

# R6: keep uploads in memory. Starlette spools file parts above 1 MB to a temporary file on disk,
# which Constitution V forbids, so the threshold is raised above the largest body accepted.
MultiPartParser.spool_max_size = BODY_LIMIT + 1


class BodyTooLarge(Exception):
    pass


class SecurityMiddleware:
    """Adds security headers to every response (R9) and refuses bodies over BODY_LIMIT unread.

    Files up to 10 MB plus form fields fit under BODY_LIMIT; the route then rejects files over
    10 MB with the form values kept. Anything larger is refused here before it is read.
    """

    def __init__(self, app: ASGIApp, on_too_large: Callable[[], bytes]):
        self.app = app
        self.on_too_large = on_too_large

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        started = False

        async def send_with_headers(message: Message) -> None:
            nonlocal started
            if message["type"] == "http.response.start":
                started = True
                headers = list(message.get("headers", []))
                headers.append((b"content-security-policy", CSP.encode()))
                headers.append((b"x-content-type-options", b"nosniff"))
                message["headers"] = headers
            await send(message)

        declared = dict(scope.get("headers", [])).get(b"content-length", b"")
        if declared.isdigit() and int(declared) > BODY_LIMIT:
            await self._reject(scope, send_with_headers)
            return

        received = 0

        async def counting_receive() -> Message:
            nonlocal received
            message = await receive()
            received += len(message.get("body", b""))
            if received > BODY_LIMIT:
                raise BodyTooLarge
            return message

        try:
            await self.app(scope, counting_receive, send_with_headers)
        except BodyTooLarge:
            if not started:
                await self._reject(scope, send_with_headers)

    async def _reject(self, scope: Scope, send: Send) -> None:
        response = HTMLResponse(self.on_too_large(), status_code=413)
        await response(scope, _empty_receive, send)


async def _empty_receive() -> Message:  # pragma: no cover - HTMLResponse never reads the body
    return {"type": "http.disconnect"}


def create_app(
    clock: Callable[[], date] = date.today,
    session_clock: Callable[[], float] = time.monotonic,
) -> FastAPI:
    """Build the app. `clock` gives the reference date; only the web layer reads the date."""
    app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
    templates = Jinja2Templates(directory=str(WEB_DIR / "templates"))
    templates.env.autoescape = True
    formatting.register(templates.env)

    app.state.templates = templates
    app.state.clock = clock
    app.state.sessions = SessionStore(session_clock)
    app.mount("/static", StaticFiles(directory=str(WEB_DIR / "static")), name="static")

    from strava_predictor.web.routes import render_too_large, router

    app.include_router(router)
    app.add_middleware(SecurityMiddleware, on_too_large=lambda: render_too_large(templates))
    return app
