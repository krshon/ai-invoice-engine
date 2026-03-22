import google.generativeai as genai
import os
from dotenv import load_dotenv

# Load API key
load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Use best extraction model
model = genai.GenerativeModel("gemini-2.5-flash")


file_path = "frontend/examples/sus.jpg"  # change if needed

with open(file_path, "rb") as f:
    image_bytes = f.read()


prompt = prompt = """
Extract invoice data STRICT JSON:

{
  "vendor": string|null,
  "invoice_no": string|null,
  "date": string|null,
  "total": string|null,
  "missing_fields": string[],
  "format_warnings": string[],
  "confidence_flags": string[]
}

Return JSON only.
"""


response = model.generate_content([
    prompt,
    {
        "mime_type": "image/png",
        "data": image_bytes
    }
])

print(response.text)