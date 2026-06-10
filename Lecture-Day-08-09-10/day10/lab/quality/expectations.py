"""
Expectation suite đơn giản (không bắt buộc Great Expectations).

Sinh viên có thể thay bằng GE / pydantic / custom — miễn là có halt có kiểm soát.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Dict, List, Tuple


@dataclass
class ExpectationResult:
    name: str
    passed: bool
    severity: str  # "warn" | "halt"
    detail: str


def run_expectations(cleaned_rows: List[Dict[str, Any]]) -> Tuple[List[ExpectationResult], bool]:
    """
    Trả về (results, should_halt).

    should_halt = True nếu có bất kỳ expectation severity halt nào fail.
    """
    results: List[ExpectationResult] = []

    # E1: có ít nhất 1 dòng sau clean
    ok = len(cleaned_rows) >= 1
    results.append(
        ExpectationResult(
            "min_one_row",
            ok,
            "halt",
            f"cleaned_rows={len(cleaned_rows)}",
        )
    )

    # E2: không doc_id rỗng
    bad_doc = [r for r in cleaned_rows if not (r.get("doc_id") or "").strip()]
    ok2 = len(bad_doc) == 0
    results.append(
        ExpectationResult(
            "no_empty_doc_id",
            ok2,
            "halt",
            f"empty_doc_id_count={len(bad_doc)}",
        )
    )

    # E3: policy refund không được chứa cửa sổ sai 14 ngày (sau khi đã fix)
    stale_refund_rows = [
        r
        for r in cleaned_rows
        if r.get("doc_id") == "policy_refund_v4"
        and re.search(r"14\s+ngày\s+làm\s+việc", str(r.get("chunk_text", "")))
    ]
    if stale_refund_rows:
        results.append(
            ExpectationResult(
                name="refund_no_stale_14d_window",
                passed=False,
                severity="halt",
                detail=f"violations={len(stale_refund_rows)}",
            )
        )
    else:
        results.append(
            ExpectationResult(
                name="refund_no_stale_14d_window",
                passed=True,
                severity="halt",
                detail="violations=0",
            )
        )

    # 4. (Tùy chọn) Kiểm tra độ dài chunk tối thiểu
    short_chunks = [
        r for r in cleaned_rows if len(str(r.get("chunk_text", "")).split()) < 8
    ]
    if short_chunks:
        results.append(
            ExpectationResult(
                name="chunk_min_length_8",
                passed=False,
                severity="warn",
                detail=f"short_chunks={len(short_chunks)}",
            )
        )
    else:
        results.append(
            ExpectationResult(
                name="chunk_min_length_8",
                passed=True,
                severity="warn",
                detail="short_chunks=0",
            )
        )

    # 5. Kiểm tra định dạng effective_date ISO 8601 (YYYY-MM-DD)
    iso_pattern = re.compile(r"^\d{4}-\d{2}-\d{2}$")
    non_iso_rows = [
        r
        for r in cleaned_rows
        if r.get("effective_date") and not iso_pattern.match(str(r.get("effective_date", "")))
    ]
    if non_iso_rows:
        results.append(
            ExpectationResult(
                name="effective_date_iso_yyyy_mm_dd",
                passed=False,
                severity="halt",
                detail=f"non_iso_rows={len(non_iso_rows)}",
            )
        )
    else:
        results.append(
            ExpectationResult(
                name="effective_date_iso_yyyy_mm_dd",
                passed=True,
                severity="halt",
                detail="non_iso_rows=0",
            )
        )

    # 6. Expectation E6: Không còn "10 ngày phép năm" trong hr_leave_policy
    stale_hr_leave_rows = [
        r
        for r in cleaned_rows
        if r.get("doc_id") == "hr_leave_policy"
        and re.search(r"10\s+ngày\s+phép\s+năm", str(r.get("chunk_text", "")), re.IGNORECASE)
    ]
    if stale_hr_leave_rows:
        results.append(
            ExpectationResult(
                name="hr_leave_no_stale_10d_annual",
                passed=False,
                severity="halt",
                detail=f"violations={len(stale_hr_leave_rows)}",
            )
        )
    else:
        results.append(
            ExpectationResult(
                name="hr_leave_no_stale_10d_annual",
                passed=True,
                severity="halt",
                detail="violations=0",
            )
        )
        
    # 7. Expectation E7: Nội dung không rõ ràng
    unclear_content_rows = [
        r
        for r in cleaned_rows
        if re.search(r"Nội\s+dung\s+không\s+rõ\s+ràng", str(r.get("chunk_text", "")), re.IGNORECASE) or "!!!" in str(r.get("chunk_text", ""))
    ]
    if unclear_content_rows:
        results.append(
            ExpectationResult(
                name="no_unclear_content_markers",
                passed=False,
                severity="halt",
                detail=f"violations={len(unclear_content_rows)}",
            )
        )
    else:
        results.append(
            ExpectationResult(
                name="no_unclear_content_markers",
                passed=True,
                severity="halt",
                detail="violations=0",
            )
        )
        
    # 8. Expectation E8: No repeated word noise
    repeated_word_rows = [
        r
        for r in cleaned_rows
        if re.search(r"(làm\s+việc\s*){2,}", str(r.get("chunk_text", "")))
    ]
    if repeated_word_rows:
        results.append(
            ExpectationResult(
                name="no_repeated_word_noise",
                passed=False,
                severity="warn",
                detail=f"violations={len(repeated_word_rows)}",
            )
        )
    else:
        results.append(
            ExpectationResult(
                name="no_repeated_word_noise",
                passed=True,
                severity="warn",
                detail="violations=0",
            )
        )
        
    # 9. Expectation E9: No repeated sentence noise
    repeated_sentence_rows = []
    for r in cleaned_rows:
        txt = str(r.get("chunk_text", ""))
        parts = txt.split(".")
        if len(parts) > 3 and parts[0].strip() == parts[1].strip():
            repeated_sentence_rows.append(r)
            
    if repeated_sentence_rows:
        results.append(
            ExpectationResult(
                name="no_repeated_sentence_noise",
                passed=False,
                severity="warn",
                detail=f"violations={len(repeated_sentence_rows)}",
            )
        )
    else:
        results.append(
            ExpectationResult(
                name="no_repeated_sentence_noise",
                passed=True,
                severity="warn",
                detail="violations=0",
            )
        )

    halt = any(not r.passed and r.severity == "halt" for r in results)
    return results, halt
