"""Timetable files: checking uploads, and fetching Google Drive links safely.

Rules (docs/02, "Files"):
- Only images (PNG, JPG, WEBP), PDFs and Excel files (.xlsx); the file's real contents
  are checked with `filetype`, not just its name.
- At most MAX_UPLOAD_MB (10 MB). Stored privately (no URL serves these files).
- Drive links: only Google's own sites, HTTPS, public files; every redirect is checked,
  so a link can't be used to reach other servers.
"""

import re
import urllib.error
import urllib.request
from urllib.parse import parse_qs, urljoin, urlparse

import filetype
from django.conf import settings
from django.core.files.base import ContentFile
from rest_framework.exceptions import ValidationError

from .models import MessageFile

XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
# Real file type -> (kind, file extension, extensions a file name may have)
ALLOWED_TYPES = {
    "image/png": (MessageFile.Kind.IMAGE, "png", {"png"}),
    "image/jpeg": (MessageFile.Kind.IMAGE, "jpg", {"jpg", "jpeg"}),
    "image/webp": (MessageFile.Kind.IMAGE, "webp", {"webp"}),
    "application/pdf": (MessageFile.Kind.PDF, "pdf", {"pdf"}),
    XLSX: (MessageFile.Kind.SPREADSHEET, "xlsx", {"xlsx"}),
}
WRONG_TYPE = "Only images (PNG, JPG, WEBP), PDFs and Excel files (.xlsx) can be used."

LINK_HOSTS = {"drive.google.com", "docs.google.com"}  # what students may paste
DOWNLOAD_HOSTS = LINK_HOSTS | {"drive.usercontent.google.com"}  # where Google may redirect
MAX_REDIRECTS = 5
TIMEOUT_SECONDS = 15


def max_bytes() -> int:
    return settings.MAX_UPLOAD_MB * 1024 * 1024


def _check_contents(data: bytes, field: str) -> tuple[str, str, str, set[str]]:
    guess = filetype.guess(data)
    if guess is None or guess.mime not in ALLOWED_TYPES:
        raise ValidationError({field: WRONG_TYPE})
    kind, extension, name_extensions = ALLOWED_TYPES[guess.mime]
    return kind, guess.mime, extension, name_extensions


def _save(
    data: bytes, *, user, kind, mime, extension, original_name="", source_url="", message=None
):
    stored = MessageFile(
        message=message,
        uploaded_by=user,
        kind=kind,
        original_name=original_name[:255],
        source_url=source_url,
        mime_type=mime,
        size_bytes=len(data),
    )
    stored.file.save(f"file.{extension}", ContentFile(data), save=False)
    stored.save()
    return stored


def save_upload(user, uploaded_file) -> MessageFile:
    """A timetable file a student uploads: checked by size, name and real contents."""
    if uploaded_file.size > max_bytes():
        raise ValidationError(
            {"file": f"The file is too large ({settings.MAX_UPLOAD_MB} MB at most)."}
        )
    data = uploaded_file.read()
    kind, mime, extension, name_extensions = _check_contents(data, "file")
    name_extension = (
        uploaded_file.name.rsplit(".", 1)[-1].lower() if "." in uploaded_file.name else ""
    )
    if name_extension not in name_extensions:
        raise ValidationError({"file": "The file's name doesn't match what's inside it."})
    return _save(
        data, user=user, kind=kind, mime=mime, extension=extension, original_name=uploaded_file.name
    )


def drive_download_url(link: str) -> str:
    """Turn a shared Google Drive / Docs link into a direct download (Docs as PDF or XLSX)."""
    parsed = urlparse(link.strip())
    if parsed.scheme != "https" or parsed.hostname not in LINK_HOSTS:
        raise ValidationError({"link": "Only Google Drive or Google Docs links can be used."})
    if parsed.hostname == "docs.google.com":
        found = re.search(r"/(document|spreadsheets|presentation)/d/([\w-]+)", parsed.path)
        if found:
            kind, file_id = found.groups()
            if kind == "spreadsheets":
                return f"https://docs.google.com/spreadsheets/d/{file_id}/export?format=xlsx"
            if kind == "document":
                return f"https://docs.google.com/document/d/{file_id}/export?format=pdf"
            return f"https://docs.google.com/presentation/d/{file_id}/export/pdf"
    else:
        found = re.search(r"/file/d/([\w-]+)", parsed.path)
        file_id = found.group(1) if found else parse_qs(parsed.query).get("id", [None])[0]
        if file_id and re.fullmatch(r"[\w-]+", file_id):
            return f"https://drive.google.com/uc?export=download&id={file_id}"
    raise ValidationError({"link": "This doesn't look like a link to a Drive file."})


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None  # redirects are followed by hand, so each new host can be checked


_opener = urllib.request.build_opener(_NoRedirect)


def _http_get(url: str) -> tuple[str | None, bytes]:
    """One HTTPS request. Returns (redirect location, None) or (None, body up to the limit)."""
    request = urllib.request.Request(url, headers={"User-Agent": "UniFlow"})
    try:
        with _opener.open(request, timeout=TIMEOUT_SECONDS) as response:
            return None, response.read(max_bytes() + 1)
    except urllib.error.HTTPError as error:
        if error.code in (301, 302, 303, 307, 308) and error.headers.get("Location"):
            return urljoin(url, error.headers["Location"]), b""
        raise ValidationError({"link": "Google didn't share this file."}) from None
    except (urllib.error.URLError, TimeoutError):
        raise ValidationError({"link": "Couldn't reach Google Drive. Try again later."}) from None


def _download(url: str) -> bytes:
    for _ in range(MAX_REDIRECTS + 1):
        parsed = urlparse(url)
        allowed_host = parsed.hostname in DOWNLOAD_HOSTS or (parsed.hostname or "").endswith(
            ".googleusercontent.com"
        )
        if parsed.scheme != "https" or not allowed_host:
            raise ValidationError({"link": "This link leads outside Google Drive."})
        location, body = _http_get(url)
        if location is None:
            return body
        url = location
    raise ValidationError({"link": "This link redirects too many times."})


def fetch_drive_link(user, link: str) -> MessageFile:
    """Download a public Google Drive / Docs file and store it like an upload."""
    data = _download(drive_download_url(link))
    if len(data) > max_bytes():
        raise ValidationError(
            {"link": f"The file is too large ({settings.MAX_UPLOAD_MB} MB at most)."}
        )
    try:
        kind, mime, extension, _ = _check_contents(data, "link")
    except ValidationError:
        # A private file comes back as Google's sign-in page instead of the file.
        raise ValidationError(
            {
                "link": "UniFlow couldn't open this link. If it only opens with your AIU "
                "account, open it, choose File → Download → Microsoft Excel (.xlsx) or PDF, "
                'and upload that file here instead. Otherwise set sharing to "Anyone with '
                'the link". ' + WRONG_TYPE
            }
        ) from None
    return _save(data, user=user, kind=kind, mime=mime, extension=extension, source_url=link)
