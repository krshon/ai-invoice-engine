import json
import re
import os
import google.generativeai as genai
from dotenv import load_dotenv


load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

model = genai.GenerativeModel("gemini-2.5-flash")


def gemini_extract(file_path):

    mime_type = (
        "application/pdf"
        if file_path.lower().endswith(".pdf")
        else "image/png"
    )

    with open(file_path, "rb") as f:
        file_bytes = f.read()


    prompt = """
You are an invoice forensic analysis assistant.

Analyze this invoice and return structured JSON.

Extract core invoice fields:

vendor
invoice_no
date
subtotal
tax
total
vendor_gst (if present)

Then detect structural anomalies:

layout_anomalies → true/false
font_inconsistencies → true/false
metadata_missing → true/false
duplicate_template_likelihood → true/false
arithmetic_inconsistency_detected → true/false
suspected_generator_patterns → true/false

Then produce explainable forensic findings:

reasons → short bullet explanations
summary → 1 sentence verdict explanation

Return ONLY valid JSON like:

{
  "vendor": "",
  "invoice_no": "",
  "date": "",
  "subtotal": "",
  "tax": "",
  "total": "",
  "vendor_gst": "",

  "layout_anomalies": false,
  "font_inconsistencies": false,
  "metadata_missing": false,
  "duplicate_template_likelihood": false,
  "arithmetic_inconsistency_detected": false,
  "suspected_generator_patterns": false,

  "reasons": [],
  "summary": ""
}
"""

    response = model.generate_content(
        [
            {
                "role": "user",
                "parts": [
                    {"text": prompt},
                    {
                        "inline_data": {
                            "mime_type": mime_type,
                            "data": file_bytes
                        }
                    }
                ]
            }
        ]
    )

    text = response.text.strip()

    if not text:
        raise ValueError("Gemini returned empty response")

    # remove markdown wrappers if present
    text = re.sub(r"```json|```", "", text).strip()

    try:
        parsed = json.loads(text)
    except Exception:
        print("Gemini raw response:")
        print(text)
        raise

    return parsed