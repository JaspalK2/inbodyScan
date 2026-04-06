"""Supabase Storage client for scan PDF uploads."""
import os
from supabase import create_client, Client


def _get_client() -> Client:
    url = os.environ["SUPABASE_URL"]
    key = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
    return create_client(url, key)


def upload_pdf(user_id: str, scan_date: str, pdf_bytes: bytes) -> str:
    """
    Upload PDF to Supabase Storage.
    Returns the storage path: scans/{user_id}/{scan_date}.pdf
    """
    client = _get_client()
    bucket = os.environ.get("SUPABASE_STORAGE_BUCKET", "scan-pdfs")
    path = f"scans/{user_id}/{scan_date}.pdf"

    client.storage.from_(bucket).upload(
        path=path,
        file=pdf_bytes,
        file_options={"content-type": "application/pdf", "upsert": "true"},
    )
    return path


def get_signed_url(storage_path: str, expires_in: int = 3600) -> str:
    """Return a time-limited signed URL for a stored PDF."""
    client = _get_client()
    bucket = os.environ.get("SUPABASE_STORAGE_BUCKET", "scan-pdfs")
    result = client.storage.from_(bucket).create_signed_url(storage_path, expires_in)
    return result["signedURL"]


def upload_csv(user_id: str, scan_date: str, csv_bytes: bytes) -> str:
    """
    Upload CSV to Supabase Storage.
    Returns the storage path: scans/{user_id}/{scan_date}.csv
    """
    client = _get_client()
    bucket = os.environ.get("SUPABASE_STORAGE_BUCKET", "scan-pdfs")
    path = f"scans/{user_id}/{scan_date}.csv"

    client.storage.from_(bucket).upload(
        path=path,
        file=csv_bytes,
        file_options={"content-type": "text/csv", "upsert": "true"},
    )
    return path
