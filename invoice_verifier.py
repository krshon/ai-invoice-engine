import re
from datetime import datetime


# =========================
# Helpers
# =========================

def parse_amount(val):
    try:
        return float(str(val).replace(",", "").replace("$", "").strip())
    except:
        return None


# =========================
# Deterministic Checks
# =========================

def check_arithmetic(data):
    subtotal = parse_amount(data.get("subtotal"))
    tax = parse_amount(data.get("tax"))
    total = parse_amount(data.get("total"))

    if subtotal is not None and tax is not None and total is not None:
        if abs((subtotal + tax) - total) > 1:
            return "arithmetic_mismatch"

    return None


def check_gst(data):
    gst = data.get("vendor_gst")

    if not gst:
        return None

    pattern = r"\d{2}[A-Z]{5}\d{4}[A-Z]\dZ\d"

    if not re.match(pattern, gst):
        return "invalid_gst_format"

    return None


def check_future_date(data):
    date_str = data.get("date")

    if not date_str:
        return None

    try:
        parsed_date = datetime.strptime(date_str, "%d/%m/%Y")

        if parsed_date > datetime.today():
            return "future_invoice_date"

    except:
        return "invalid_date_format"

    return None


def check_vendor_anomaly(data, vendor_stats=None):

    if not vendor_stats:
        return None

    vendor = data.get("vendor")
    total = parse_amount(data.get("total"))

    if vendor in vendor_stats and total:

        mean = vendor_stats[vendor]["mean"]
        std = vendor_stats[vendor]["std"]

        if abs(total - mean) > 2 * std:
            return "vendor_amount_anomaly"

    return None


# =========================
# Main Verifier
# =========================

def verify_invoice(data, vendor_stats=None):

    score = 100

    signals = {
        "missing_fields": [],
        "format_warnings": [],
        "confidence_flags": [],
        "risk_breakdown": {},
        "summary": data.get("summary"),
        "reasons": data.get("reasons", [])
    }

    # =========================
    # Missing required fields
    # =========================

    required = ["invoice_no", "date", "total", "vendor"]

    for field in required:
        if not data.get(field):
            signals["missing_fields"].append(field)
            score -= 12


    # =========================
    # Placeholder vendor detection
    # =========================

    vendor = str(data.get("vendor", "")).lower()

    suspicious_vendors = [
        "logo",
        "unknown",
        "sample",
        "test",
        "demo",
        "add company name"
    ]

    if vendor in suspicious_vendors:
        signals["confidence_flags"].append("placeholder_vendor_detected")
        score -= 25


    # =========================
    # Arithmetic validation
    # =========================

    arithmetic_issue = check_arithmetic(data)

    if arithmetic_issue:
        signals["confidence_flags"].append(arithmetic_issue)
        signals["risk_breakdown"][arithmetic_issue] = -35
        score -= 35


    # =========================
    # GST validation
    # =========================

    gst_issue = check_gst(data)

    if gst_issue:
        signals["format_warnings"].append(gst_issue)
        signals["risk_breakdown"][gst_issue] = -15
        score -= 15


    # =========================
    # Date validation
    # =========================

    date_issue = check_future_date(data)

    if date_issue:
        signals["format_warnings"].append(date_issue)
        signals["risk_breakdown"][date_issue] = -12
        score -= 12


    # =========================
    # Vendor anomaly detection
    # =========================

    vendor_issue = check_vendor_anomaly(data, vendor_stats)

    if vendor_issue:
        signals["confidence_flags"].append(vendor_issue)
        signals["risk_breakdown"][vendor_issue] = -20
        score -= 20


    # =========================
    # Gemini forensic anomaly flags
    # =========================

    gemini_flags = {
        "layout_anomalies": 12,
        "font_inconsistencies": 10,
        "metadata_missing": 15,
        "duplicate_template_likelihood": 18,
        "suspected_generator_patterns": 20
    }

    for flag, penalty in gemini_flags.items():

        if data.get(flag):

            score -= penalty
            signals["confidence_flags"].append(flag)
            signals["risk_breakdown"][flag] = -penalty


    # =========================
    # Duplicate invoice detection (optional hook)
    # =========================

    if data.get("duplicate_invoice_detected"):
        score -= 25
        signals["confidence_flags"].append("duplicate_invoice_detected")
        signals["risk_breakdown"]["duplicate_invoice_detected"] = -25


    # =========================
    # Summary alignment penalty
    # =========================

    summary = str(data.get("summary", "")).lower()

    if "high fraud risk" in summary:
        score -= 20

    elif "moderate fraud risk" in summary:
        score -= 10


    score = max(0, min(100, round(score)))


    # =========================
    # Classification
    # =========================

    if score >= 80:
        label = "LIKELY LEGIT"

    elif score >= 50:
        label = "NEEDS REVIEW"

    else:
        label = "SUSPICIOUS"


    return {
        "label": label,
        "score": score,
        "signals": signals
    }