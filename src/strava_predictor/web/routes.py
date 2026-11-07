"""Routes only validate input, call the domain, and render results (Constitution VI)."""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from starlette.datastructures import UploadFile

from strava_predictor import config
from strava_predictor.domain.analysis import analyse
from strava_predictor.domain.models import Activity, DataError
from strava_predictor.domain.parsing import parse_activities
from strava_predictor.web.forms import FIELDS, validate

router = APIRouter()

COOKIE = "session"
TOO_LARGE = f"The file is larger than {config.MAX_UPLOAD_BYTES // (1024 * 1024)} MB."
NO_FILE = "Choose your Strava activities CSV."
UPLOAD_AGAIN = "Please upload your CSV again; the earlier upload has expired."
UNREADABLE = "The file could not be read: it is not a UTF-8 text file."


def default_values() -> dict[str, str]:
    values = dict.fromkeys(FIELDS, "")
    values["max_hr"] = str(config.MAX_HR_DEFAULT)
    return values


def _stored(request: Request) -> tuple[Activity, ...] | None:
    return request.app.state.sessions.get(request.cookies.get(COOKIE))


def _form(
    request: Request,
    status: int,
    values: dict[str, str],
    has_data: bool,
    errors: dict[str, str] | None = None,
    data_error: str | None = None,
) -> HTMLResponse:
    return request.app.state.templates.TemplateResponse(
        request,
        "form.html",
        {
            "values": values,
            "errors": errors or {},
            "data_error": data_error,
            "has_data": has_data,
        },
        status_code=status,
    )


def render_too_large(templates: Jinja2Templates) -> bytes:
    """Page for bodies refused before they are read, so no form values can be kept."""
    template = templates.env.get_template("form.html")
    return template.render(
        values=default_values(), errors={"csv_file": TOO_LARGE}, data_error=None, has_data=False
    ).encode("utf-8")


@router.get("/", response_class=HTMLResponse)
async def form_page(request: Request) -> HTMLResponse:
    return _form(request, 200, default_values(), has_data=_stored(request) is not None)


@router.post("/results", response_class=HTMLResponse)
async def results(request: Request) -> HTMLResponse:
    form = await request.form()
    form_result = validate({name: str(form.get(name) or "") for name in FIELDS})
    values, errors = form_result.values, dict(form_result.errors)
    stored = _stored(request)
    has_data = stored is not None

    upload = form.get("csv_file")
    file_bytes = None
    if isinstance(upload, UploadFile) and upload.filename:
        file_bytes = await upload.read()
        if len(file_bytes) > config.MAX_UPLOAD_BYTES:
            errors["csv_file"] = TOO_LARGE
            return _form(request, 413, values, has_data, errors)
    if file_bytes is None and stored is None:
        errors["csv_file"] = UPLOAD_AGAIN if request.cookies.get(COOKIE) else NO_FILE
    if errors:
        return _form(request, 400, values, has_data, errors)

    try:
        if file_bytes is not None:
            activities = tuple(parse_activities(file_bytes.decode("utf-8-sig")))
        else:
            activities = stored
        result = analyse(activities, form_result.inputs, request.app.state.clock())
    except UnicodeDecodeError:
        return _form(request, 400, values, has_data, data_error=UNREADABLE)
    except DataError as error:
        return _form(request, 400, values, has_data, data_error=error.message)

    token = request.cookies.get(COOKIE)
    if file_bytes is not None:
        token = request.app.state.sessions.put(activities, token=token)

    response = request.app.state.templates.TemplateResponse(
        request,
        "results.html",
        {
            "values": values,
            "errors": {},
            "data_error": None,
            "has_data": True,
            "inputs": form_result.inputs,
            "input_warnings": form_result.warnings,
            "result": result,
        },
    )
    response.set_cookie(COOKIE, token, httponly=True, samesite="strict", path="/")
    return response
