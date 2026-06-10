"""
Cleaning rules — raw export → cleaned rows + quarantine.

Baseline gồm các failure mode mở rộng (allowlist doc_id, parse ngày, HR stale version).
Sinh viên thêm ≥3 rule mới: mỗi rule phải ghi `metric_impact` (xem README — chống trivial).
"""

from __future__ import annotations

import csv
import hashlib
import re
from pathlib import Path
from typing import Any, Dict, List, Tuple

# Khớp export hợp lệ trong lab (mở rộng khi nhóm thêm doc mới — phải đồng bộ contract).
ALLOWED_DOC_IDS = frozenset(
    {
        "policy_refund_v4",
        "sla_p1_2026",
        "it_helpdesk_faq",
        "hr_leave_policy",
        "access_control_sop",
    }
)

_ISO_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_DMY_SLASH = re.compile(r"^(\d{2})/(\d{2})/(\d{4})$")


def _norm_text(s: str) -> str:
    return " ".join((s or "").strip().split()).lower()


def _stable_chunk_id(doc_id: str, chunk_text: str, seq: int) -> str:
    h = hashlib.sha256(f"{doc_id}|{chunk_text}|{seq}".encode("utf-8")).hexdigest()[:16]
    return f"{doc_id}_{seq}_{h}"


def _normalize_effective_date(raw: str) -> Tuple[str, str]:
    """
    Trả về (iso_date, error_reason).
    iso_date rỗng nếu không parse được.
    """
    s = (raw or "").strip().replace(".", "").replace(" ", "")
    if not s:
        return "", "empty_effective_date"
    if _ISO_DATE.match(s):
        return s, ""
    m = _DMY_SLASH.match(s)
    if m:
        dd, mm, yyyy = m.group(1), m.group(2), m.group(3)
        return f"{yyyy}-{mm}-{dd}", ""
    return "", "invalid_effective_date_format"


def load_raw_csv(path: Path) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    with path.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append({k: (v or "").strip() for k, v in r.items()})
    return rows


def clean_rows(
    rows: List[Dict[str, str]],
    *,
    apply_refund_window_fix: bool = True,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Trả về (cleaned, quarantine).

    Baseline (mở rộng theo narrative Day 10):
    1) Quarantine: doc_id không thuộc allowlist (export lạ / catalog sai).
    2) Chuẩn hoá effective_date sang YYYY-MM-DD; quarantine nếu không parse được.
    3) Quarantine: chunk hr_leave_policy có effective_date < 2026-01-01 (bản HR cũ / conflict version).
    4) Quarantine: chunk_text rỗng hoặc effective_date rỗng sau chuẩn hoá.
    5) Loại trùng nội dung chunk_text (giữ bản đầu).
    6) Fix stale refund: policy_refund_v4 chứa '14 ngày làm việc' → 7 ngày.
    """
    quarantine: List[Dict[str, Any]] = []
    seen_text: set[str] = set()
    cleaned: List[Dict[str, Any]] = []
    seq = 0

    for raw in rows:
        doc_id = raw.get("doc_id", "")
        text = raw.get("chunk_text", "")
        eff_raw = raw.get("effective_date", "")
        exported_at = raw.get("exported_at", "")

        if doc_id not in ALLOWED_DOC_IDS:
            quarantine.append({**raw, "reason": "unknown_doc_id"})
            continue

        eff_norm, eff_err = _normalize_effective_date(eff_raw)
        if eff_err == "empty_effective_date":
            quarantine.append({**raw, "reason": "missing_effective_date"})
            continue
        if eff_err == "invalid_effective_date_format":
            quarantine.append({**raw, "reason": eff_err, "effective_date_raw": eff_raw})
            continue

        if doc_id == "hr_leave_policy" and eff_norm < "2026-01-01":
            quarantine.append(
                {
                    **raw,
                    "reason": "stale_hr_policy_effective_date",
                    "effective_date_normalized": eff_norm,
                }
            )
            continue

        if not text:
            quarantine.append({**raw, "reason": "missing_chunk_text"})
            continue

        key = _norm_text(text)
        if key in seen_text:
            quarantine.append({**raw, "reason": "duplicate_chunk_text"})
            continue
        seen_text.add(key)

        fixed_text = text
        if apply_refund_window_fix and doc_id == "policy_refund_v4":
            if re.search(r"14\s+ngày\s+làm\s+việc", fixed_text):
                fixed_text = re.sub(
                    r"14\s+ngày\s+làm\s+việc",
                    "7 ngày làm việc",
                    fixed_text
                )
                fixed_text += " [cleaned: stale_refund_window]"

        # New Rule 1: Lọc bỏ nội dung không rõ ràng
        # metric_impact: loại bỏ rác/nhiễu
        if re.search(r"Nội\s+dung\s+không\s+rõ\s+ràng", text, re.IGNORECASE) or "!!!" in text:
            quarantine.append({**raw, "reason": "unclear_content"})
            continue
            
        # New Rule 2: Xóa các marker "10 ngày phép năm" trong bản cũ (stale policy) mà lọt qua bộ lọc ngày
        # metric_impact: đảm bảo tính chính xác của hr_leave_policy theo expectation E6
        if doc_id == "hr_leave_policy" and re.search(r"10\s+ngày\s+phép\s+năm", text, re.IGNORECASE):
            quarantine.append({**raw, "reason": "stale_10d_annual_leave"})
            continue
            
        # New Rule 3: Tránh lỗi trùng lặp text dài bất thường (lặp cấu trúc)
        # metric_impact: giảm deduplication noise
        if len(text.split(".")) > 3 and text.split(".")[0].strip() == text.split(".")[1].strip():
            quarantine.append({**raw, "reason": "repeated_sentence_noise"})
            continue
            
        # New Rule 4: Fix text lặp từ "làm việc làm việc"
        # metric_impact: làm thay đổi cleaned_records (sửa string noise) thay vì loại bỏ
        if re.search(r"(làm\s+việc\s*){2,}", fixed_text):
            fixed_text = re.sub(r"(làm\s+việc\s*){2,}", "làm việc ", fixed_text).replace(" .", ".")
            fixed_text += " [cleaned: repeated_word_noise]"
            
        # Tweak để cải thiện retrieval: Chuyển "Escalation P1" thành "Ticket P1"
        if re.search(r"Escalation\s+P1:", fixed_text, re.IGNORECASE):
            fixed_text = re.sub(r"Escalation\s+P1:", "Ticket P1 escalation:", fixed_text, flags=re.IGNORECASE)

        # Semantic Chunking: Tôn trọng ranh giới câu (Sentence Boundary)
        # Thay vì cắt mù quáng theo đúng 50 từ, thuật toán tách theo dấu chấm câu
        # để đảm bảo không một câu nào bị chẻ làm đôi, phá vỡ ngữ nghĩa.
        sentences = re.split(r'(?<=[.!?])\s+', fixed_text)
        max_words_per_chunk = 70
        
        sub_chunks = []
        current_chunk = []
        current_len = 0
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence: continue
            
            word_count = len(sentence.split())
            # Nếu thêm câu này vượt quá giới hạn và chunk hiện tại đã có dữ liệu
            if current_len + word_count > max_words_per_chunk and current_chunk:
                sub_chunks.append(" ".join(current_chunk))
                # Overlap: Mềm dẻo giữ lại câu cuối cùng của chunk trước đó để làm cầu nối
                current_chunk = [current_chunk[-1], sentence]
                current_len = len(current_chunk[0].split()) + word_count
            else:
                current_chunk.append(sentence)
                current_len += word_count
                
        if current_chunk:
            sub_chunks.append(" ".join(current_chunk))

        for sub_chunk in sub_chunks:
            seq += 1
            cleaned.append(
                {
                    "chunk_id": _stable_chunk_id(doc_id, sub_chunk, seq),
                    "doc_id": doc_id,
                    "chunk_text": sub_chunk,
                    "effective_date": eff_norm,
                    "exported_at": exported_at or "",
                }
            )

    return cleaned, quarantine


def write_cleaned_csv(path: Path, rows: List[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("chunk_id,doc_id,chunk_text,effective_date,exported_at\n", encoding="utf-8")
        return
    fieldnames = ["chunk_id", "doc_id", "chunk_text", "effective_date", "exported_at"]
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in fieldnames})


def write_quarantine_csv(path: Path, rows: List[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("chunk_id,doc_id,chunk_text,effective_date,exported_at,reason\n", encoding="utf-8")
        return
    keys: List[str] = []
    seen_k: set[str] = set()
    for r in rows:
        for k in r.keys():
            if k not in seen_k:
                seen_k.add(k)
                keys.append(k)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys, extrasaction="ignore", restval="")
        w.writeheader()
        for r in rows:
            w.writerow(r)
