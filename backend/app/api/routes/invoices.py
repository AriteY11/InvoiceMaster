from __future__ import annotations

import csv
import hashlib
import io
import shutil
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Optional

from urllib.parse import quote

from fastapi import APIRouter, Body, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ...config import UPLOAD_DIR, settings
from ...db import get_db
from ...models.invoice import Invoice
from ...models.invoice_item import InvoiceItem
from ...schemas.invoice import (
    DeleteInvoiceResponse,
    InvoiceDetailRead,
    InvoiceListResponse,
    InvoiceSummaryRead,
    UploadInvoiceResult,
    UploadInvoicesResponse,
)
from ...services.invoice_parser import parse_invoice
from ...services.pdf_extractor import extract_pdf

router = APIRouter(prefix="/api/invoices", tags=["invoices"])


def _compute_file_hash(file_path: Path) -> str:
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


@router.post("/upload", response_model=UploadInvoicesResponse)
async def upload_invoices(
    files: list[UploadFile] = File(...),
    db: Session = Depends(get_db),
) -> UploadInvoicesResponse:
    results: list[UploadInvoiceResult] = []

    for file in files:
        if not file.filename:
            results.append(UploadInvoiceResult(
                file_name="unknown", status="error", message="文件名为空"
            ))
            continue

        ext = Path(file.filename).suffix.lower()
        if ext not in settings.allowed_extensions:
            results.append(UploadInvoiceResult(
                file_name=file.filename, status="error", message=f"不支持的文件格式: {ext}"
            ))
            continue

        content = await file.read()
        file_size_mb = len(content) / (1024 * 1024)
        if file_size_mb > settings.max_upload_size_mb:
            results.append(UploadInvoiceResult(
                file_name=file.filename, status="error",
                message=f"文件过大: {file_size_mb:.1f}MB (上限 {settings.max_upload_size_mb}MB)"
            ))
            continue

        temp_path = UPLOAD_DIR / file.filename
        try:
            with open(temp_path, "wb") as f:
                f.write(content)

            file_hash = _compute_file_hash(temp_path)

            existing = db.query(Invoice).filter(Invoice.file_hash == file_hash).first()
            if existing:
                results.append(UploadInvoiceResult(
                    file_name=file.filename, status="duplicate", message="该发票已存在",
                    invoice_id=existing.id, duplicate=True,
                ))
                continue

            extraction = extract_pdf(temp_path)
            invoice_data = parse_invoice(extraction)

            invoice = Invoice(
                file_name=file.filename,
                stored_file_name=file.filename,
                file_path=str(temp_path),
                file_hash=file_hash,
                page_count=extraction.page_count,
                invoice_name=invoice_data.get("invoice_name"),
                invoice_code=invoice_data.get("invoice_code"),
                invoice_number=invoice_data.get("invoice_number"),
                issue_date=invoice_data.get("issue_date"),
                check_code=invoice_data.get("check_code"),
                machine_number=invoice_data.get("machine_number"),
                invoice_type=invoice_data.get("invoice_type"),
                buyer_name=invoice_data.get("buyer_name"),
                buyer_tax_number=invoice_data.get("buyer_tax_number"),
                buyer_address_phone=invoice_data.get("buyer_address_phone"),
                buyer_bank_account=invoice_data.get("buyer_bank_account"),
                seller_name=invoice_data.get("seller_name"),
                seller_tax_number=invoice_data.get("seller_tax_number"),
                seller_address_phone=invoice_data.get("seller_address_phone"),
                seller_bank_account=invoice_data.get("seller_bank_account"),
                amount_excluding_tax=invoice_data.get("amount_excluding_tax"),
                tax_amount=invoice_data.get("tax_amount"),
                total_amount=invoice_data.get("total_amount"),
                total_amount_text=invoice_data.get("total_amount_text"),
                remarks=invoice_data.get("remarks"),
                raw_text=invoice_data.get("raw_text"),
                parser_warnings=invoice_data.get("parser_warnings", []),
                parse_confidence=invoice_data.get("parse_confidence", 0.0),
                parse_status="parsed",
            )
            db.add(invoice)
            db.flush()

            for item_data in invoice_data.get("items", []):
                item = InvoiceItem(
                    invoice_id=invoice.id,
                    line_no=item_data.get("line_no", 1),
                    item_name=item_data.get("item_name"),
                    specification=item_data.get("specification"),
                    unit=item_data.get("unit"),
                    quantity=item_data.get("quantity"),
                    unit_price=item_data.get("unit_price"),
                    amount=item_data.get("amount"),
                    tax_rate=item_data.get("tax_rate"),
                    tax_amount=item_data.get("tax_amount"),
                )
                db.add(item)

            db.commit()

            results.append(UploadInvoiceResult(
                file_name=file.filename, status="success",
                message=f"解析完成 (置信度: {invoice_data.get('parse_confidence', 0):.0%})",
                invoice_id=invoice.id,
            ))

        except Exception as e:
            db.rollback()
            results.append(UploadInvoiceResult(
                file_name=file.filename, status="error", message=f"解析失败: {str(e)}"
            ))

    return UploadInvoicesResponse(results=results)


@router.get("", response_model=InvoiceListResponse)
def list_invoices(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    keyword: Optional[str] = Query(None),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    amount_min: Optional[float] = Query(None),
    amount_max: Optional[float] = Query(None),
    seller_name: Optional[str] = Query(None),
    invoice_type: Optional[str] = Query(None),
    uploaded_from: Optional[date] = Query(None),
    uploaded_to: Optional[date] = Query(None),
    db: Session = Depends(get_db),
) -> InvoiceListResponse:
    query = _build_invoice_query(
        db, keyword, date_from, date_to, amount_min, amount_max,
        seller_name, invoice_type, uploaded_from, uploaded_to,
    )

    total = query.count()
    invoices = (
        query.order_by(Invoice.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    items = [
        InvoiceSummaryRead(
            id=inv.id,
            file_name=inv.file_name,
            invoice_name=inv.invoice_name,
            invoice_code=inv.invoice_code,
            invoice_number=inv.invoice_number,
            issue_date=inv.issue_date,
            invoice_type=inv.invoice_type,
            buyer_name=inv.buyer_name,
            seller_name=inv.seller_name,
            total_amount=inv.total_amount,
            tax_amount=inv.tax_amount,
            parse_status=inv.parse_status,
            parse_confidence=inv.parse_confidence,
            created_at=inv.created_at,
        )
        for inv in invoices
    ]

    return InvoiceListResponse(items=items, total=total, page=page, page_size=page_size)


EXPORT_FIELDS = [
    "invoice_name", "invoice_code", "invoice_number", "issue_date",
    "check_code", "machine_number", "invoice_type", "currency",
    "buyer_name", "buyer_tax_number", "buyer_address_phone", "buyer_bank_account",
    "seller_name", "seller_tax_number", "seller_address_phone", "seller_bank_account",
    "amount_excluding_tax", "tax_amount", "total_amount", "total_amount_text",
    "remarks", "file_name", "page_count",
    "parse_status", "parse_confidence", "parser_warnings",
    "created_at",
]
EXPORT_HEADERS = [
    "发票名称", "发票代码", "发票号码", "开票日期",
    "校验码", "机器编号", "发票类型", "币种",
    "购买方名称", "购买方纳税人识别号", "购买方地址电话", "购买方开户行及账号",
    "销售方名称", "销售方纳税人识别号", "销售方地址电话", "销售方开户行及账号",
    "不含税金额", "税额", "价税合计", "价税合计(大写)",
    "备注", "文件名称", "PDF页数",
    "解析状态", "解析置信度", "解析警告",
    "上传时间",
]


def _build_invoice_query(
    db: Session,
    keyword: Optional[str] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    amount_min: Optional[float] = None,
    amount_max: Optional[float] = None,
    seller_name: Optional[str] = None,
    invoice_type: Optional[str] = None,
    uploaded_from: Optional[date] = None,
    uploaded_to: Optional[date] = None,
):
    query = db.query(Invoice)
    if keyword:
        like = f"%{keyword}%"
        query = query.filter(
            (Invoice.file_name.ilike(like)) |
            (Invoice.invoice_code.ilike(like)) |
            (Invoice.invoice_number.ilike(like)) |
            (Invoice.buyer_name.ilike(like)) |
            (Invoice.seller_name.ilike(like))
        )
    if date_from:
        query = query.filter(Invoice.issue_date >= date_from)
    if date_to:
        query = query.filter(Invoice.issue_date <= date_to)
    if amount_min is not None:
        query = query.filter(Invoice.total_amount >= Decimal(str(amount_min)))
    if amount_max is not None:
        query = query.filter(Invoice.total_amount <= Decimal(str(amount_max)))
    if seller_name:
        query = query.filter(Invoice.seller_name.ilike(f"%{seller_name}%"))
    if invoice_type:
        query = query.filter(Invoice.invoice_type.ilike(f"%{invoice_type}%"))
    if uploaded_from:
        query = query.filter(Invoice.created_at >= datetime.combine(uploaded_from, datetime.min.time()))
    if uploaded_to:
        query = query.filter(Invoice.created_at <= datetime.combine(uploaded_to, datetime.max.time()))
    return query


def _format_row(inv: Invoice) -> list[str]:
    return [
        inv.invoice_name or "",
        inv.invoice_code or "",
        inv.invoice_number or "",
        str(inv.issue_date) if inv.issue_date else "",
        inv.check_code or "",
        inv.machine_number or "",
        inv.invoice_type or "",
        inv.currency or "",
        inv.buyer_name or "",
        inv.buyer_tax_number or "",
        inv.buyer_address_phone or "",
        inv.buyer_bank_account or "",
        inv.seller_name or "",
        inv.seller_tax_number or "",
        inv.seller_address_phone or "",
        inv.seller_bank_account or "",
        str(inv.amount_excluding_tax) if inv.amount_excluding_tax is not None else "",
        str(inv.tax_amount) if inv.tax_amount is not None else "",
        str(inv.total_amount) if inv.total_amount is not None else "",
        inv.total_amount_text or "",
        inv.remarks or "",
        inv.file_name or "",
        str(inv.page_count) if inv.page_count else "",
        inv.parse_status or "",
        f"{inv.parse_confidence:.0%}" if inv.parse_confidence else "",
        "; ".join(inv.parser_warnings) if inv.parser_warnings else "",
        str(inv.created_at.replace(microsecond=0)) if inv.created_at else "",
    ]


@router.get("/export")
def export_invoices(
    keyword: Optional[str] = Query(None),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    amount_min: Optional[float] = Query(None),
    amount_max: Optional[float] = Query(None),
    seller_name: Optional[str] = Query(None),
    invoice_type: Optional[str] = Query(None),
    uploaded_from: Optional[date] = Query(None),
    uploaded_to: Optional[date] = Query(None),
    format: str = Query("xlsx", pattern=r"^(csv|xlsx)$"),
    columns: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    query = _build_invoice_query(
        db, keyword, date_from, date_to, amount_min, amount_max,
        seller_name, invoice_type, uploaded_from, uploaded_to,
    )
    invoices = query.order_by(Invoice.created_at.desc()).all()
    all_rows = [_format_row(inv) for inv in invoices]

    if columns:
        selected = [c.strip() for c in columns.split(",") if c.strip()]
        index_map = {k: i for i, k in enumerate(EXPORT_FIELDS)}
        col_indices = [index_map[k] for k in selected if k in index_map]
        headers = [EXPORT_HEADERS[i] for i in col_indices]
        rows = []
        for row in all_rows:
            rows.append([row[i] for i in col_indices])
    else:
        headers = list(EXPORT_HEADERS)
        rows = all_rows

    now_str = datetime.now().strftime("%Y%m%d_%H%M%S")

    if format == "xlsx":
        import openpyxl
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "发票导出"
        ws.append(headers)
        for row in rows:
            ws.append(row)
        buf = io.BytesIO()
        wb.save(buf)
        buf.seek(0)
        return StreamingResponse(
            buf,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename=invoices_{now_str}.xlsx"},
        )

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(headers)
    writer.writerows(rows)
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=invoices_{now_str}.csv"},
    )


class ManualInvoiceCreate(BaseModel):
    invoice_name: str | None = None
    invoice_code: str | None = None
    invoice_number: str | None = None
    issue_date: date | None = None
    check_code: str | None = None
    machine_number: str | None = None
    invoice_type: str | None = None
    buyer_name: str | None = None
    buyer_tax_number: str | None = None
    buyer_address_phone: str | None = None
    buyer_bank_account: str | None = None
    seller_name: str | None = None
    seller_tax_number: str | None = None
    seller_address_phone: str | None = None
    seller_bank_account: str | None = None
    amount_excluding_tax: float | None = None
    tax_amount: float | None = None
    total_amount: float | None = None
    total_amount_text: str | None = None
    remarks: str | None = None


@router.post("/manual", response_model=UploadInvoicesResponse)
def create_manual_invoices(
    invoices: list[ManualInvoiceCreate] = Body(...),
    db: Session = Depends(get_db),
) -> UploadInvoicesResponse:
    results: list[UploadInvoiceResult] = []
    for i, data in enumerate(invoices):
        label = data.invoice_number or data.invoice_name or f"手动录入 {i + 1}"
        try:
            inv = Invoice(
                file_name=f"手动录入-{label}",
                parse_status="manual",
                parse_confidence=1.0,
                invoice_name=data.invoice_name,
                invoice_code=data.invoice_code,
                invoice_number=data.invoice_number,
                issue_date=data.issue_date,
                check_code=data.check_code,
                machine_number=data.machine_number,
                invoice_type=data.invoice_type,
                buyer_name=data.buyer_name,
                buyer_tax_number=data.buyer_tax_number,
                buyer_address_phone=data.buyer_address_phone,
                buyer_bank_account=data.buyer_bank_account,
                seller_name=data.seller_name,
                seller_tax_number=data.seller_tax_number,
                seller_address_phone=data.seller_address_phone,
                seller_bank_account=data.seller_bank_account,
                amount_excluding_tax=Decimal(str(data.amount_excluding_tax)) if data.amount_excluding_tax is not None else None,
                tax_amount=Decimal(str(data.tax_amount)) if data.tax_amount is not None else None,
                total_amount=Decimal(str(data.total_amount)) if data.total_amount is not None else None,
                total_amount_text=data.total_amount_text,
                remarks=data.remarks,
            )
            db.add(inv)
            db.commit()
            db.refresh(inv)
            results.append(UploadInvoiceResult(
                file_name=label,
                invoice_id=inv.id,
                status="success",
                message="已创建",
            ))
        except Exception as e:
            db.rollback()
            results.append(UploadInvoiceResult(
                file_name=label,
                status="error",
                message=f"创建失败: {str(e)}",
            ))
    return UploadInvoicesResponse(results=results)


class FilterValuesResponse(BaseModel):
    sellers: list[str]
    invoice_types: list[str]


@router.get("/filters", response_model=FilterValuesResponse)
def get_filter_values(db: Session = Depends(get_db)):
    sellers = [
        r[0] for r in db.query(Invoice.seller_name)
        .filter(Invoice.seller_name.isnot(None), Invoice.seller_name != "")
        .distinct()
        .order_by(Invoice.seller_name)
        .all()
    ]
    types = [
        r[0] for r in db.query(Invoice.invoice_type)
        .filter(Invoice.invoice_type.isnot(None), Invoice.invoice_type != "")
        .distinct()
        .order_by(Invoice.invoice_type)
        .all()
    ]
    return FilterValuesResponse(sellers=sellers, invoice_types=types)


@router.get("/{invoice_id}/file")
def download_invoice_file(invoice_id: int, db: Session = Depends(get_db)):
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="发票不存在")
    file_path = Path(invoice.file_path) if invoice.file_path else None
    if not file_path or not file_path.exists():
        raise HTTPException(status_code=404, detail="PDF文件不存在")
    encoded_filename = quote(invoice.file_name or "invoice.pdf")
    return FileResponse(
        path=str(file_path),
        media_type="application/pdf",
        filename=invoice.file_name,
        headers={
            "Content-Disposition": f"inline; filename*=UTF-8''{encoded_filename}",
        },
    )


@router.get("/{invoice_id}", response_model=InvoiceDetailRead)
def get_invoice(invoice_id: int, db: Session = Depends(get_db)) -> InvoiceDetailRead:
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="发票不存在")
    return InvoiceDetailRead.model_validate(invoice)


@router.delete("/{invoice_id}", response_model=DeleteInvoiceResponse)
def delete_invoice(invoice_id: int, db: Session = Depends(get_db)) -> DeleteInvoiceResponse:
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="发票不存在")
    db.delete(invoice)
    db.commit()
    return DeleteInvoiceResponse(message="发票已删除")
