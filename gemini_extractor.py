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
You are an invoice fraud detection assistant.

Analyze this invoice and return structured JSON.

Extract:

vendor
invoice_no
date
total

Then estimate fraud indicators (0–100 risk scale):

template_risk
layout_risk
font_risk
arithmetic_risk
metadata_risk
vendor_risk
generator_risk

Then produce explainable forensic findings:

reasons → list of short human-readable explanations
summary → 1 sentence verdict explanation

Return ONLY valid JSON like:

{
  "vendor": "",
  "invoice_no": "",
  "date": "",
  "total": "",

  "template_risk": 0,
  "layout_risk": 0,
  "font_risk": 0,
  "arithmetic_risk": 0,
  "metadata_risk": 0,
  "vendor_risk": 0,
  "generator_risk": 0,

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