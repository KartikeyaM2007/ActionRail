"""
Invoice text and field extraction helpers.

Design philosophy:
- Extraction is best-effort and never required. The product works without it.
- Uncertain fields are left blank; the upload form always lets the user override.
- No external services, no OCR packages in this module.
- All regex patterns are conservative: a miss is safer than a wrong value.
- Phase 2C: safer amount and currency extraction; bare-number fallback removed;
  currency now requires explicit symbol/code evidence, not just substring match.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# PDF text extraction
# ---------------------------------------------------------------------------

def extract_text_from_pdf(path: Path) -> tuple[str | None, str]:
    """
    Extract plain text from a digital PDF using pypdf.

    Returns (text, status_note).
    status_note is one of:
      "ok"                        — text extracted
      "empty"                     — PDF parsed but no text found
      "not_a_pdf"                 — file is not a valid PDF
      "extraction_error:<msg>"    — pypdf raised an exception
    """
    try:
        from pypdf import PdfReader  # lazy import so module loads without pypdf installed

        reader = PdfReader(str(path))
        pages = []
        for page in reader.pages:
            t = page.extract_text()
            if t:
                pages.append(t)
        if not pages:
            return None, "empty"
        return "\n".join(pages).strip(), "ok"
    except Exception as exc:
        msg = str(exc)[:120]
        if "PdfReadError" in type(exc).__name__ or "invalid" in msg.lower():
            return None, "not_a_pdf"
        return None, f"extraction_error:{msg}"


def extraction_status_for_image(content_type: str | None) -> str:
    """
    Utility that describes image extraction status without running OCR.
    Kept for backward compatibility and utility use.
    """
    ct = (content_type or "").lower()
    if any(ct.startswith(p) for p in ("image/png", "image/jpeg", "image/jpg")):
        return "not_available_without_ocr"
    return "unsupported_type"


# ---------------------------------------------------------------------------
# Invoice ID patterns
# ---------------------------------------------------------------------------

_INVOICE_ID_PATTERNS = [
    # "Invoice #84652373" or "Invoice No: INV-2001" — stop at word boundary
    r"(?:invoice\s*(?:no\.?|number|#|id|:)[:\s]+)([A-Z0-9][-A-Z0-9/]{1,20})",
    r"(?:inv(?:oice)?\s*(?:no\.?|number|#)[:\s]+)([A-Z0-9][-A-Z0-9/]{1,20})",
    # Pure INV-/BILL- prefixed IDs
    r"\b(INV[-/]?[\d]{3,})\b",
    r"\b(BILL[-/]?[\d]{3,})\b",
    # Bare numeric IDs after "Invoice no:" e.g. "Invoice no: 84652373"
    r"(?:invoice\s*no\.?[:\s]+)([\d]{5,12})",
]

# ---------------------------------------------------------------------------
# Date patterns
# ---------------------------------------------------------------------------

_DATE_PATTERNS = [
    # YYYY-MM-DD
    r"\b(\d{4}-\d{2}-\d{2})\b",
    # MM/DD/YYYY or DD/MM/YYYY
    r"\b(\d{1,2}/\d{1,2}/\d{4})\b",
    # DD-MM-YYYY
    r"\b(\d{1,2}-\d{1,2}-\d{4})\b",
    # Jan 15, 2026  or  June 13, 2026  or  15 January 2026
    r"\b(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{4})\b",
    r"\b((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{1,2},?\s+\d{4})\b",
]

# ---------------------------------------------------------------------------
# GST
# ---------------------------------------------------------------------------

_GST_PATTERNS = [
    r"\b([0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1})\b",
]

# ---------------------------------------------------------------------------
# Currency detection — explicit evidence required
# ---------------------------------------------------------------------------

# Each entry: (regex_pattern_that_must_match, code)
# Patterns are tested with re.search on the full text.
# INR: ₹ symbol or INR code or "Rs." or "rupees" — must be a standalone token.
# USD: $ symbol or USD code or "US DOLLAR" — must not be inside a state name.
# NOT included: bare "IN" (appears in US address as Indiana abbreviation).
_CURRENCY_PATTERNS: list[tuple[str, str]] = [
    # INR — explicit symbol or code
    (r"₹",                                          "INR"),
    (r"\bINR\b",                                    "INR"),
    (r"\bRs\.?\b",                                  "INR"),
    (r"\bRupees?\b",                                "INR"),
    # USD — explicit symbol or code
    (r"\$",                                         "USD"),
    (r"\bUSD\b",                                    "USD"),
    (r"\bUS\s+DOLLARS?\b",                          "USD"),
    # EUR
    (r"€",                                          "EUR"),
    (r"\bEUR\b",                                    "EUR"),
    # GBP
    (r"£",                                          "GBP"),
    (r"\bGBP\b",                                    "GBP"),
]

def _detect_currency(text: str) -> str | None:
    """
    Detect currency from explicit evidence only.
    Does NOT infer INR from state abbreviations like 'IN', or USD from US addresses.
    Returns the currency code if found, else None.
    """
    for pattern, code in _CURRENCY_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return code
    return None

# ---------------------------------------------------------------------------
# Amount extraction — confidence-gated, no bare-number fallback
# ---------------------------------------------------------------------------

# Lines that indicate we are on a quantity / row-number / non-amount line.
# Amounts on these lines are rejected.
_AMOUNT_REJECT_LABEL_PATTERN = re.compile(
    r"^\s*(?:qty|quantity|no\.?|item\s+no\.?|tax\s+id|iban|date|invoice\s+no|zip|postal)",
    re.IGNORECASE,
)

# High-confidence amount label patterns (ordered by preference).
# Each entry is (label_regex, priority) — lower priority number = preferred.
_AMOUNT_LABEL_PATTERNS: list[tuple[str, int]] = [
    (r"amount\s*due",    1),
    (r"balance\s*due",   1),
    (r"total\s*due",     1),
    (r"grand\s*total",   1),
    (r"invoice\s*total", 1),
    (r"total\s*amount",  1),
    (r"amount\s*payable",1),
    (r"net\s*payable",   1),
    (r"subtotal",        2),
    (r"total",           3),  # Weakest — only accepted if accompanied by a currency symbol
]

# Numeric value patterns (capture group 1 = the raw number string)
_AMOUNT_VALUE_PATTERNS = [
    # With currency symbol immediately attached: $1,234.56 or ₹83,000 or Rs. 1,234
    r"(?:Rs\.?|INR|₹)\s*([\d,]+(?:\.\d{1,2})?)",
    r"\$\s*([\d]{1,3}(?:,[\d]{3})*(?:\.\d{1,2})?)",
    r"(?:USD|EUR|GBP)\s*([\d,]+(?:\.\d{1,2})?)",
    # Numeric with decimal — e.g. "1,234.56" or "83000.00"
    r"\b([\d]{1,3}(?:,[\d]{3})*\.\d{2})\b",
    # Numeric with comma thousands separator, no decimal — e.g. "1,234" (min 4 digits)
    r"\b([\d]{1,3}(?:,[\d]{3})+)\b",
    # Plain integer of at least 4 digits — fallback for INR amounts like "83000"
    r"\b([\d]{4,10})\b",
]


def _parse_amount(raw: str | None) -> float | None:
    if not raw:
        return None
    try:
        cleaned = raw.strip().replace(",", "")
        val = float(cleaned)
        return val if val > 0 else None
    except ValueError:
        return None


def _extract_value_from_line(line: str) -> float | None:
    """Extract the first plausible monetary value from a line, after a label."""
    for pattern in _AMOUNT_VALUE_PATTERNS:
        m = re.search(pattern, line, re.IGNORECASE)
        if m:
            val = _parse_amount(m.group(1))
            if val is not None and val >= 10:  # Reject implausibly small amounts
                return val
    return None


def _extract_amount_with_confidence(text: str) -> tuple[float | None, list[str]]:
    """
    Extract invoice amount using only high-confidence labelled lines or
    explicit currency-prefixed numbers.
    Returns (amount_or_None, list_of_notes).

    Strategy:
    1. Search each line for a high-confidence label (amount due, grand total, etc.).
    2. Also accept currency-symbol-prefixed numbers ($ or ₹ or INR etc.) as
       medium-confidence (priority 2) even without a label — the explicit symbol
       is enough to distinguish from bare item quantities.
    3. Among all candidates, prefer the lowest priority number (most specific).
    4. Reject values < 10 (implausible).
    5. If nothing found, return (None, [note]).
    """
    notes: list[str] = []
    candidates: list[tuple[int, float, str]] = []  # (priority, value, matched_line)

    lines = text.splitlines()

    # Currency-symbol-prefixed amounts (priority 2, no label required).
    # These are safe to extract because the explicit symbol rules out quantities.
    _CURRENCY_PREFIXED = [
        (r"(?:Rs\.?|INR|₹)\s*([\d,]+(?:\.\d{1,2})?)",          2),
        (r"\$\s*([\d]{1,3}(?:,[\d]{3})*(?:\.\d{1,2})?)",       2),
        (r"(?:USD|EUR|GBP)\s*([\d,]+(?:\.\d{1,2})?)",           2),
    ]

    for line in lines:
        if _AMOUNT_REJECT_LABEL_PATTERN.match(line):
            continue
        line_lower = line.lower()

        # High-confidence labels first
        for label_pattern, priority in _AMOUNT_LABEL_PATTERNS:
            if re.search(label_pattern, line_lower):
                val = _extract_value_from_line(line)
                if val is not None:
                    candidates.append((priority, val, line.strip()[:80]))
                break  # One label match per line

        # Currency-prefixed numbers (only if no label already matched this line)
        else:
            for pattern, priority in _CURRENCY_PREFIXED:
                m = re.search(pattern, line, re.IGNORECASE)
                if m:
                    val = _parse_amount(m.group(1))
                    if val is not None and val >= 10:
                        candidates.append((priority, val, line.strip()[:80]))
                    break

    if not candidates:
        notes.append("Manual review required: amount not confidently extracted from labelled line.")
        notes.append("Skipped amount extraction: no high-confidence total label found.")
        return None, notes

    # Sort by priority (ascending = most specific first), then by value (descending = largest)
    candidates.sort(key=lambda x: (x[0], -x[1]))
    best_priority, best_val, best_line = candidates[0]

    # Weak label ("total" with priority 3) only accepted if a currency symbol is on that line
    if best_priority == 3:
        if not re.search(r"[\$₹€£]|\b(?:USD|INR|EUR|GBP)\b", best_line, re.IGNORECASE):
            notes.append(
                "Skipped amount from 'total' line: no currency symbol present. "
                "Manual review required: amount not confidently extracted."
            )
            return None, notes

    notes.append(f"Extracted amount (confidence level {best_priority}): {best_val}")
    return best_val, notes

# ---------------------------------------------------------------------------
# Vendor extraction
# ---------------------------------------------------------------------------

_SKIP_VENDOR_WORDS = frozenset({
    "invoice", "bill", "bill to", "sold to", "ship to", "shipping",
    "to:", "from:", "total", "subtotal", "amount", "date", "due",
    "tax", "vat", "gst", "payment", "description", "qty", "quantity",
    "price", "unit", "items", "no", "number", "thank", "please",
    "page", "www", "http", "address", "client", "seller", "buyer",
    "item", "product", "service", "balance", "receipt",
})


def _try_extract_vendor(lines: list[str]) -> str | None:
    """
    Try to infer vendor from the first few non-empty, non-generic lines.
    Returns None if nothing confident is found.
    This is intentionally conservative — a wrong vendor is worse than no vendor.
    """
    for line in lines[:8]:
        stripped = line.strip().rstrip(".,:")
        if not stripped or len(stripped) < 3 or stripped.isdigit():
            continue
        lower = stripped.lower()
        if any(skip in lower for skip in _SKIP_VENDOR_WORDS):
            continue
        # Skip lines that look like addresses (digits + street keywords)
        if re.search(r"\d{1,5}\s+\w+\s+(st|ave|blvd|rd|ln|dr|way|hwy)\b", lower):
            continue
        return stripped
    return None


# ---------------------------------------------------------------------------
# Public API — extract_fields_from_text()
# ---------------------------------------------------------------------------

def _first_match(text: str, patterns: list[str], flags: int = re.IGNORECASE) -> str | None:
    for pattern in patterns:
        m = re.search(pattern, text, flags)
        if m:
            return m.group(1).strip()
    return None


def extract_fields_from_text(text: str) -> dict[str, Any]:
    """
    Attempt to extract invoice fields from plain text using conservative regex.

    Returns a dict with keys:
      "fields"  — dict of extracted values (only confidently detected fields are included)
      "notes"   — list of human-readable notes about what was/wasn't found

    Return shape is unchanged from previous versions. Callers that check
    result["fields"] and result["notes"] continue to work without modification.
    """
    notes: list[str] = []
    fields: dict[str, Any] = {}

    # --- Invoice ID ---
    inv_id = _first_match(text, _INVOICE_ID_PATTERNS)
    if inv_id:
        fields["invoice_id"] = inv_id.strip()
        notes.append(f"Extracted invoice_id: {inv_id.strip()}")
    else:
        notes.append("invoice_id not confidently detected — enter manually")

    # --- Amount (confidence-gated) ---
    amount, amount_notes = _extract_amount_with_confidence(text)
    notes.extend(amount_notes)
    if amount is not None:
        fields["amount"] = amount

    # --- Currency (explicit evidence only) ---
    currency = _detect_currency(text)
    if currency:
        fields["currency"] = currency
        notes.append(f"Detected currency: {currency}")
    else:
        notes.append("currency not confidently detected — enter manually or leave as INR default")

    # --- Dates ---
    all_dates: list[str] = []
    for pattern in _DATE_PATTERNS:
        for m in re.finditer(pattern, text, re.IGNORECASE):
            candidate = m.group(1).strip()
            if candidate not in all_dates:
                all_dates.append(candidate)
        if len(all_dates) >= 2:
            break
    if all_dates:
        fields["invoice_date"] = all_dates[0]
        notes.append(f"First date found (used as invoice_date): {all_dates[0]}")
    if len(all_dates) >= 2:
        fields["due_date"] = all_dates[1]
        notes.append(f"Second date found (used as due_date): {all_dates[1]}")

    # --- GST ---
    gst = _first_match(text, _GST_PATTERNS)
    if gst:
        fields["gst_number"] = gst
        notes.append(f"Extracted GST number: {gst}")

    # --- Vendor (best-effort; conservative) ---
    lines = text.splitlines()
    vendor = _try_extract_vendor(lines)
    if vendor:
        fields["vendor"] = vendor
        notes.append(f"Inferred vendor (unconfirmed — verify manually): {vendor}")
    else:
        notes.append("vendor not confidently detected — enter manually")

    return {"fields": fields, "notes": notes}
