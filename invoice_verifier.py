import re
import random


def verify_invoice(data):

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
    # Missing field penalties
    # =========================
    required = ["invoice_no", "date", "total", "vendor"]

    for field in required:
        if not data.get(field):
            signals["missing_fields"].append(field)
            score -= 20


    # =========================
    # Vendor placeholder detection
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
        score -= 35


    # =========================
    # Date validation
    # =========================
    date = data.get("date")

    if date:
        if not re.match(r"\d{1,2}[/\- ]?[A-Za-z0-9]+[/\- ]?\d{2,4}", str(date)):
            signals["format_warnings"].append("invalid_date_format")
            score -= 15


    # =========================
    # Total validation
    # =========================
    total = data.get("total")

    if total:
        try:
            float(str(total).replace(",", "").replace("$", ""))
        except:
            signals["format_warnings"].append("invalid_total_amount")
            score -= 20


    # =========================
    # Gemini weighted fraud scoring
    # =========================

    risk_weights = {
        "template_risk": 0.30,
        "generator_risk": 0.35,
        "metadata_risk": 0.25,
        "vendor_risk": 0.20,
        "layout_risk": 0.10,
        "font_risk": 0.08,
        "arithmetic_risk": 0.40
    }

    for risk_key, weight in risk_weights.items():

        risk_value = data.get(risk_key, 0)

        penalty = risk_value * weight

        score -= penalty

        if penalty > 10:
            signals["confidence_flags"].append(risk_key)

        signals["risk_breakdown"][risk_key] = round(-penalty, 2)


    # =========================
    # Strong explanation alignment penalty
    # =========================

    if data.get("summary"):

        summary = data["summary"].lower()

        if "high fraud risk" in summary:
            score -= 25

        elif "moderate fraud risk" in summary:
            score -= 12


    # =========================
    # Entropy smoothing (small realism noise)
    # =========================

    score += random.uniform(-2, 2)


    score = max(0, min(100, round(score)))


    # =========================
    # Classification
    # =========================

    if score >= 80:
        label = "LIKELY LEGIT"

    elif score >= 45:
        label = "NEEDS REVIEW"

    else:
        label = "SUSPICIOUS"


    return {
        "label": label,
        "score": score,
        "signals": signals
    }