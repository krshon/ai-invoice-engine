def verify_invoice(data):
    score = 100

    required = ["invoice_no", "date", "total", "vendor"]
    for field in required:
        if field not in data or not data[field]:
            score -= 20  # missing field → drop score

    # Scoring categories
    if score >= 85:
        label = "LIKELY LEGIT"
    elif score >= 60:
        label = "NEEDS REVIEW"
    else:
        label = "SUSPICIOUS / INCOMPLETE"

    return label, score
