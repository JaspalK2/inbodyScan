from datetime import date
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..schemas.scan import ScanOut, ScanWithMetrics, MetricOut
from ..services.scan_service import (
    create_scan, save_metrics, get_scan_by_id,
    get_scans_for_user, get_metrics_for_scan, scan_date_exists,
)
from ..services.pdf_extractor import extract_metrics
from ..storage.supabase_storage import upload_pdf, get_signed_url
from ..db.session import get_db
from shared.python.auth_utils.dependencies import get_current_user_id

router = APIRouter(prefix="/api/scans", tags=["scans"])

MAX_PDF_SIZE = 10 * 1024 * 1024  # 10 MB


@router.post("/upload", response_model=ScanWithMetrics, status_code=status.HTTP_201_CREATED)
async def upload_scan(
    file: UploadFile = File(...),
    scan_date: date = Form(...),
    user_id: str = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db),
):
    if file.content_type not in ("application/pdf",):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File must be a PDF")

    pdf_bytes = await file.read()
    if len(pdf_bytes) > MAX_PDF_SIZE:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="PDF exceeds 10 MB limit")

    if await scan_date_exists(session, user_id, scan_date):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A scan for this date already exists",
            headers={"X-Error-Code": "duplicate_scan_date"},
        )

    storage_path = upload_pdf(user_id, str(scan_date), pdf_bytes)
    metrics_dict = extract_metrics(pdf_bytes)

    scan = await create_scan(session, user_id, scan_date, storage_path)
    metric_records = await save_metrics(session, scan.id, metrics_dict)

    return ScanWithMetrics(
        scan=ScanOut.model_validate(scan),
        metrics=[MetricOut.model_validate(m) for m in metric_records],
    )


@router.get("/", response_model=list[ScanOut])
async def list_scans(user_id: str = Depends(get_current_user_id), session: AsyncSession = Depends(get_db)):
    return await get_scans_for_user(session, user_id)


@router.get("/{scan_id}", response_model=ScanWithMetrics)
async def get_scan(scan_id: str, user_id: str = Depends(get_current_user_id), session: AsyncSession = Depends(get_db)):
    scan = await get_scan_by_id(session, scan_id, user_id)
    if not scan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scan not found")
    metrics = await get_metrics_for_scan(session, scan_id)
    return ScanWithMetrics(
        scan=ScanOut.model_validate(scan),
        metrics=[MetricOut.model_validate(m) for m in metrics],
    )


@router.get("/{scan_id}/download-url")
async def scan_download_url(scan_id: str, user_id: str = Depends(get_current_user_id), session: AsyncSession = Depends(get_db)):
    scan = await get_scan_by_id(session, scan_id, user_id)
    if not scan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scan not found")
    url = get_signed_url(scan.storage_path)
    return {"url": url, "expires_in": 3600}
