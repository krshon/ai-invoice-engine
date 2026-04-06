import re
from datetime import datetime


# =========================
# Helpers
# =========================

def parse_amount(val):
    try:
        return float(str(val).replace(",", "").replace("$", "").replace("₹", "").strip())
    except Exception:
        return None


def clamp(value, lo=0, hi=100):
    return max(lo, min(hi, value))


# =========================
# Gemini confidence parser
# =========================

# Maps Gemini's summary phrase → (score_override_or_None, base_penalty)
_GEMINI_RISK_LEVELS = {
    "high fraud risk":     ("SUSPICIOUS",    30),
    "likely fraudulent":   ("SUSPICIOUS",    30),
    "serious concerns":    (None,            22),
    "moderate fraud risk": (None,            15),
    "some concerns":       (None,            10),
    "minor issues":        (None,             5),
    "low risk":            (None,             0),
    "appears legitimate":  (None,            -5),   # bonus: Gemini says it looks fine
    "likely legit":        (None,            -8),
    "legitimate invoice":  (None,           -10),
}

# Gemini forensic flag → penalty (ordered by severity)
_GEMINI_FLAG_PENALTIES = {
    "suspected_generator_patterns":  22,
    "duplicate_template_likelihood": 20,
    "metadata_missing":              15,
    "layout_anomalies":              12,
    "font_inconsistencies":          10,
}

# Keywords in Gemini `reasons` that raise confidence a field is genuinely missing
# vs just an extraction failure
_EXTRACTION_FAILURE_HINTS = {
    "could not extract",
    "not found in document",
    "field not present",
    "no invoice number",
    "no date",
    "no total",
    "no vendor",
    "unreadable",
    "blurry",
    "cut off",
}

# Vendors that are clearly placeholder / template defaults
_PLACEHOLDER_VENDORS = {
    "logo", "unknown", "sample", "test", "demo",
    "add company name", "company name", "your company",
    "acme", "example", "n/a", "na", "none",
}


# =========================
# Deterministic checks
# =========================

def check_arithmetic(data):
    subtotal = parse_amount(data.get("subtotal"))
    tax      = parse_amount(data.get("tax"))
    total    = parse_amount(data.get("total"))

    if subtotal is not None and tax is not None and total is not None:
        expected = round(subtotal + tax, 2)
        actual   = round(total, 2)
        diff     = abs(expected - actual)

        if diff > 1.0:
            severity = "arithmetic_mismatch_major" if diff > total * 0.05 else "arithmetic_mismatch_minor"
            return severity, diff
    return None, None


def check_gst(data):
    gst = data.get("vendor_gst")
    if not gst:
        return None

    # Correct Indian GST format: 2-digit state + 5-letter PAN + 4-digit + 1-letter + 1-digit + Z + 1-digit
    pattern = r"^\d{2}[A-Z]{5}\d{4}[A-Z][1-9A-Z]Z[0-9]$"
    if not re.match(pattern, str(gst).strip()):
        return "invalid_gst_format"
    return None


def check_future_date(data):
    date_str = data.get("date")
    if not date_str:
        return None

    for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y", "%m/%d/%Y"):
        try:
            parsed_date = datetime.strptime(str(date_str).strip(), fmt)
            if parsed_date > datetime.today():
                return "future_invoice_date"
            # Flag invoices more than 5 years old as suspicious
            if (datetime.today() - parsed_date).days > 365 * 5:
                return "unusually_old_date"
            return None
        except ValueError:
            continue
    return "invalid_date_format"


def check_vendor_anomaly(data, vendor_stats=None):
    if not vendor_stats:
        return None, None

    vendor = data.get("vendor")
    total  = parse_amount(data.get("total"))

    if vendor in vendor_stats and total is not None:
        mean = vendor_stats[vendor]["mean"]
        std  = vendor_stats[vendor]["std"]
        if std > 0:
            z_score = abs(total - mean) / std
            if z_score > 3:
                return "vendor_amount_anomaly_severe", z_score
            if z_score > 2:
                return "vendor_amount_anomaly", z_score
    return None, None


# =========================
# Gemini signal parser
# =========================

def parse_gemini_summary(summary: str):
    """
    Returns (label_override_or_None, penalty) based on Gemini's summary.
    Searches for all matching phrases and returns the most severe match.
    """
    summary_lower = str(summary).lower()
    best_penalty  = 0
    best_override = None

    for phrase, (override, penalty) in _GEMINI_RISK_LEVELS.items():
        if phrase in summary_lower:
            if penalty > best_penalty:
                best_penalty  = penalty
                best_override = override

    return best_override, best_penalty


def parse_gemini_reasons(reasons):
    """
    Analyses Gemini's reasons list for:
      - extraction failure hints (reduces missing-field penalty)
      - additional fraud signals mentioned in text
    Returns (is_extraction_issue: bool, extra_penalty: int)
    """
    if not reasons or not isinstance(reasons, list):
        return False, 0

    combined = " ".join(str(r) for r in reasons).lower()

    is_extraction_issue = any(hint in combined for hint in _EXTRACTION_FAILURE_HINTS)

    extra_penalty = 0
    if "tampered" in combined or "altered" in combined:
        extra_penalty += 18
    if "duplicate" in combined or "already submitted" in combined:
        extra_penalty += 20
    if "suspicious" in combined or "fraudulent" in combined:
        extra_penalty += 15
    if "inflated" in combined or "overcharged" in combined:
        extra_penalty += 12
    if "template" in combined or "generated" in combined:
        extra_penalty += 10
    if "missing signature" in combined or "no authorisation" in combined:
        extra_penalty += 8

    return is_extraction_issue, extra_penalty


# =========================
# Invoice identity check
# =========================

def is_invoice_document(data):
    """
    Returns True if the document looks like an invoice at all.
    Uses both keyword scan on raw_text and presence of structured fields.
    """
    invoice_keywords = [
        "invoice", "bill to", "invoice number", "invoice no",
        "total", "amount due", "gst", "tax invoice",
        "payable", "receipt", "purchase order",
    ]
    text = str(data.get("raw_text", "")).lower()
    keyword_hits = sum(1 for k in invoice_keywords if k in text)

    # Also count structured fields present as weak evidence
    field_hits = sum(1 for f in ["invoice_no", "date", "total", "vendor"] if data.get(f))

    return (keyword_hits >= 2) or (keyword_hits >= 1 and field_hits >= 2)


# =========================
# Main verifier
# =========================

def verify_invoice(data, vendor_stats=None):

    # ── Stage 0: Is this even an invoice? ──────────────────────────────────
    if not is_invoice_document(data):
        return {
            "label": "NOT AN INVOICE",
            "score": 0,
            "signals": {
                "missing_fields":    [],
                "format_warnings":   [],
                "confidence_flags":  ["not_invoice_document"],
                "risk_breakdown":    {"not_invoice_document": -100},
                "summary":          "Document does not appear to be an invoice",
                "reasons":          [],
                "gemini_risk_level": "unknown",
            }
        }

    score = 100
    signals = {
        "missing_fields":    [],
        "format_warnings":   [],
        "confidence_flags":  [],
        "risk_breakdown":    {},
        "summary":           data.get("summary", ""),
        "reasons":           data.get("reasons", []),
        "gemini_risk_level": "unknown",
    }

    # ── Stage 1: Parse Gemini signals first ───────────────────────────────
    # This informs how harshly we penalise missing fields (extraction issue vs truly absent)

    gemini_override, gemini_summary_penalty = parse_gemini_summary(data.get("summary", ""))
    is_extraction_issue, gemini_reason_penalty = parse_gemini_reasons(data.get("reasons"))

    # Determine Gemini risk level label for reporting
    _, raw_penalty = parse_gemini_summary(data.get("summary", ""))
    if raw_penalty >= 25:
        signals["gemini_risk_level"] = "high"
    elif raw_penalty >= 12:
        signals["gemini_risk_level"] = "moderate"
    elif raw_penalty <= -5:
        signals["gemini_risk_level"] = "low"
    else:
        signals["gemini_risk_level"] = "unclear"

    # Apply Gemini summary penalty (but cap at 35 to avoid double-counting with flags)
    if gemini_summary_penalty > 0:
        capped = min(gemini_summary_penalty, 35)
        score -= capped
        signals["risk_breakdown"]["gemini_summary_risk"] = -capped
    elif gemini_summary_penalty < 0:
        # Positive signal from Gemini — small bonus
        bonus = abs(gemini_summary_penalty)
        score += bonus
        signals["risk_breakdown"]["gemini_positive_signal"] = bonus

    # Apply Gemini reason-derived penalty
    if gemini_reason_penalty > 0:
        score -= gemini_reason_penalty
        signals["risk_breakdown"]["gemini_reason_flags"] = -gemini_reason_penalty

    # ── Stage 2: Missing required fields ──────────────────────────────────
    required_fields = ["invoice_no", "date", "total", "vendor"]
    # Penalty is halved when Gemini indicates this is likely an extraction/OCR issue
    field_penalty = 6 if is_extraction_issue else 12

    for field in required_fields:
        if not data.get(field):
            signals["missing_fields"].append(field)
            score -= field_penalty
            signals["risk_breakdown"][f"missing_{field}"] = -field_penalty

    # ── Stage 3: Placeholder vendor ───────────────────────────────────────
    vendor = str(data.get("vendor", "")).strip().lower()
    if vendor in _PLACEHOLDER_VENDORS:
        signals["confidence_flags"].append("placeholder_vendor_detected")
        signals["risk_breakdown"]["placeholder_vendor_detected"] = -25
        score -= 25

    # ── Stage 4: Arithmetic validation ────────────────────────────────────
    arith_issue, diff = check_arithmetic(data)
    if arith_issue:
        penalty = 40 if arith_issue == "arithmetic_mismatch_major" else 25
        signals["confidence_flags"].append(arith_issue)
        signals["risk_breakdown"][arith_issue] = -penalty
        score -= penalty

    # ── Stage 5: GST format ───────────────────────────────────────────────
    gst_issue = check_gst(data)
    if gst_issue:
        signals["format_warnings"].append(gst_issue)
        signals["risk_breakdown"][gst_issue] = -15
        score -= 15

    # ── Stage 6: Date validation ──────────────────────────────────────────
    date_issue = check_future_date(data)
    if date_issue:
        penalty = 20 if date_issue == "future_invoice_date" else 12
        signals["format_warnings"].append(date_issue)
        signals["risk_breakdown"][date_issue] = -penalty
        score -= penalty

    # ── Stage 7: Vendor anomaly detection ────────────────────────────────
    vendor_issue, z_score = check_vendor_anomaly(data, vendor_stats)
    if vendor_issue:
        penalty = 25 if "severe" in vendor_issue else 15
        signals["confidence_flags"].append(vendor_issue)
        signals["risk_breakdown"][vendor_issue] = -penalty
        if z_score:
            signals["risk_breakdown"][f"{vendor_issue}_zscore"] = round(z_score, 2)
        score -= penalty

    # ── Stage 8: Gemini forensic flags (weighted by severity) ────────────
    for flag, penalty in _GEMINI_FLAG_PENALTIES.items():
        if data.get(flag):
            signals["confidence_flags"].append(flag)
            signals["risk_breakdown"][flag] = -penalty
            score -= penalty

    # ── Stage 9: Duplicate invoice ────────────────────────────────────────
    if data.get("duplicate_invoice_detected"):
        signals["confidence_flags"].append("duplicate_invoice_detected")
        signals["risk_breakdown"]["duplicate_invoice_detected"] = -30
        score -= 30

    # ── Stage 10: Gemini confidence score integration ─────────────────────
    # If Gemini provides an explicit confidence score (0-100), blend it
    gemini_confidence = data.get("gemini_confidence_score")
    if gemini_confidence is not None:
        try:
            gc = float(gemini_confidence)
            # Blend: 70% our deterministic score, 30% Gemini's confidence
            blended = round(0.70 * score + 0.30 * gc)
            signals["risk_breakdown"]["gemini_confidence_blend"] = round(gc)
            score = blended
        except (TypeError, ValueError):
            pass

    # ── Final clamping ────────────────────────────────────────────────────
    score = clamp(round(score))

    # ── Classification ────────────────────────────────────────────────────
    # Allow Gemini override for obvious fraud, but only push DOWN not UP
    if gemini_override == "SUSPICIOUS":
        label = "SUSPICIOUS"
    elif score >= 80:
        label = "LIKELY LEGIT"
    elif score >= 50:
        label = "NEEDS REVIEW"
    else:
        label = "SUSPICIOUS"

    return {
        "label":  label,
        "score":  score,
        "signals": signals,
    }