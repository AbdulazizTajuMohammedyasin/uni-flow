import io
import zipfile

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.exceptions import ValidationError

from apps.accounts.services import create_user
from apps.intelligence import files
from apps.intelligence.files import drive_download_url, fetch_drive_link, save_upload

pytestmark = pytest.mark.django_db

PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64
PDF = b"%PDF-1.7\n1 0 obj\n<<>>\nendobj\n%%EOF\n"
EXE = b"MZ\x90\x00" + b"\x00" * 64
HTML = b"<!DOCTYPE html><html><body>Sign in - Google Accounts</body></html>"


def xlsx_bytes() -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("[Content_Types].xml", "<Types/>")
        archive.writestr("xl/workbook.xml", "<workbook/>")
    return buffer.getvalue()


@pytest.fixture(autouse=True)
def private_media(settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path  # never write test files into backend/media


@pytest.fixture
def student():
    return create_user("ali@student.aiu.edu.my", "Str0ng-pass-99", full_name="Ali")


def upload(name, data):
    return SimpleUploadedFile(name, data)


# --- Uploads -------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("name", "data", "kind", "mime"),
    [
        ("timetable.png", PNG, "image", "image/png"),
        ("Timetable Sem 2.PDF", PDF, "pdf", "application/pdf"),
        ("timetable.xlsx", xlsx_bytes(), "spreadsheet", files.XLSX),
    ],
)
def test_real_timetable_files_are_kept_privately(student, settings, name, data, kind, mime):
    stored = save_upload(student, upload(name, data))

    assert (stored.kind, stored.mime_type, stored.size_bytes) == (kind, mime, len(data))
    assert stored.uploaded_by == student
    assert stored.original_name == name
    assert stored.file.name.startswith("message_files/")
    assert name.split(".")[0] not in stored.file.name  # random name, not the original
    assert (settings.MEDIA_ROOT / stored.file.name).read_bytes() == data


def test_a_renamed_program_is_refused(student):
    with pytest.raises(ValidationError) as error:
        save_upload(student, upload("timetable.pdf", EXE))
    assert "Only images" in str(error.value.detail["file"])


def test_a_name_that_does_not_match_the_contents_is_refused(student):
    with pytest.raises(ValidationError) as error:
        save_upload(student, upload("timetable.png", PDF))
    assert "doesn't match" in str(error.value.detail["file"])


def test_files_over_the_limit_are_refused(student, settings):
    settings.MAX_UPLOAD_MB = 1
    with pytest.raises(ValidationError):
        save_upload(student, upload("big.pdf", PDF + b"0" * (1024 * 1024)))


# --- Google Drive links ----------------------------------------------------------------


@pytest.mark.parametrize(
    ("link", "download"),
    [
        (
            "https://drive.google.com/file/d/1AbC-d_9/view?usp=sharing",
            "https://drive.google.com/uc?export=download&id=1AbC-d_9",
        ),
        (
            "https://drive.google.com/open?id=1AbC-d_9",
            "https://drive.google.com/uc?export=download&id=1AbC-d_9",
        ),
        (
            "https://docs.google.com/spreadsheets/d/1XyZ/edit#gid=0",
            "https://docs.google.com/spreadsheets/d/1XyZ/export?format=xlsx",
        ),
        (
            "https://docs.google.com/document/d/1XyZ/edit",
            "https://docs.google.com/document/d/1XyZ/export?format=pdf",
        ),
    ],
)
def test_drive_links_become_direct_downloads(link, download):
    assert drive_download_url(link) == download


@pytest.mark.parametrize(
    "link",
    [
        "http://drive.google.com/file/d/1AbC/view",  # not HTTPS
        "https://drive.google.com.evil.example/file/d/1AbC/view",  # look-alike host
        "https://example.com/timetable.pdf",
        "https://drive.google.com/drive/folders/1AbC",  # a folder, not a file
    ],
)
def test_other_links_are_refused(link):
    with pytest.raises(ValidationError):
        drive_download_url(link)


def fake_google(monkeypatch, answers: dict):
    """Pretend to be Google: each URL answers with ("redirect", url) or ("body", bytes)."""

    def http_get(url):
        kind, value = answers[url]
        return (value, b"") if kind == "redirect" else (None, value)

    monkeypatch.setattr(files, "_http_get", http_get)


LINK = "https://drive.google.com/file/d/1AbC/view?usp=sharing"
DOWNLOAD = "https://drive.google.com/uc?export=download&id=1AbC"
CONTENT = "https://drive.usercontent.google.com/download?id=1AbC"


def test_a_public_drive_file_is_downloaded_through_googles_redirects(student, monkeypatch):
    fake_google(monkeypatch, {DOWNLOAD: ("redirect", CONTENT), CONTENT: ("body", PDF)})

    stored = fetch_drive_link(student, LINK)
    assert (stored.kind, stored.source_url, stored.size_bytes) == ("pdf", LINK, len(PDF))


def test_a_private_drive_file_gets_a_clear_message(student, monkeypatch):
    fake_google(monkeypatch, {DOWNLOAD: ("body", HTML)})
    with pytest.raises(ValidationError) as error:
        fetch_drive_link(student, LINK)
    assert "Anyone with the link" in str(error.value.detail["link"])


def test_redirects_outside_google_are_refused(student, monkeypatch):
    fake_google(monkeypatch, {DOWNLOAD: ("redirect", "https://10.0.0.5/internal")})
    with pytest.raises(ValidationError) as error:
        fetch_drive_link(student, LINK)
    assert "outside Google Drive" in str(error.value.detail["link"])


def test_endless_redirects_are_refused(student, monkeypatch):
    fake_google(monkeypatch, {DOWNLOAD: ("redirect", DOWNLOAD)})
    with pytest.raises(ValidationError):
        fetch_drive_link(student, LINK)
