import fitz  # PyMuPDF
from PIL import Image, ImageEnhance
from transformers import DonutProcessor, VisionEncoderDecoderModel
import easyocr
import io
import json
import re
import numpy as np


# -------------------------
# Load DONUT model
# -------------------------

MODEL_NAME = "naver-clova-ix/donut-base-finetuned-cord-v2"

processor = DonutProcessor.from_pretrained(MODEL_NAME)
model = VisionEncoderDecoderModel.from_pretrained(MODEL_NAME)


# -------------------------
# Load EasyOCR fallback
# -------------------------

reader = easyocr.Reader(['en'], gpu=False)


TASK_PROMPT = "<s>invoice information extraction</s>"


# -------------------------
# Image Preprocessing
# -------------------------

def preprocess_image(img):

    img = img.convert("RGB")

    img = img.resize((1280, 1280))

    img = ImageEnhance.Contrast(img).enhance(1.5)

    img = ImageEnhance.Sharpness(img).enhance(1.3)

    return img


# -------------------------
# Normalize extracted fields
# -------------------------

def normalize_fields(data):

    mapping = {
        "invoice_number": "invoice_no",
        "supplier": "vendor",
        "seller": "vendor",
        "company": "vendor",
        "total_amount": "total",
        "amount_total": "total"
    }

    normalized = {}

    for key, value in data.items():

        new_key = mapping.get(key, key)

        normalized[new_key] = value

    return normalized


# -------------------------
# EasyOCR fallback extraction
# -------------------------

def hybrid_extract(img):

    img_np = np.array(img)

    text_lines = reader.readtext(img_np, detail=False)

    raw_text = "\n".join(text_lines)


    # Normalize decimal format
    clean_text = raw_text.replace(",", ".").replace(" ", "")


    # Extract total amount
    amount = re.search(r'\$?\d{2,8}\.\d{2}', clean_text)


    # Extract vendor (first meaningful line)
    vendor = None

    vendor_candidates = [
        line.strip()
        for line in raw_text.split("\n")
        if len(line.strip()) > 2
    ]

    for candidate in vendor_candidates:

        if "invoice" not in candidate.lower():

            vendor = candidate

            break


    # Extract invoice number
    invoice_no = re.search(r'(INV[- ]?\d+)', raw_text)


    # Extract date
    date = re.search(r'\d{2}/\d{2}/\d{4}', raw_text)


    return {
        "raw_text": raw_text,
        "vendor": vendor,
        "total": amount.group(0) if amount else None,
        "invoice_no": invoice_no.group(0) if invoice_no else None,
        "date": date.group(0) if date else None
    }


# -------------------------
# Main extraction function
# -------------------------

def donut_extract(file_path):

    images = []


    # Convert PDF pages to images
    if file_path.lower().endswith(".pdf"):

        pdf = fitz.open(file_path)

        for page in pdf:

            pix = page.get_pixmap()

            img = Image.open(io.BytesIO(pix.tobytes("png")))

            images.append(preprocess_image(img))

        pdf.close()


    # Handle image input
    else:

        img = Image.open(file_path)

        images.append(preprocess_image(img))


    results = []


    # Process each page/image
    for img in images:

        try:

            pixel_values = processor(
                img,
                TASK_PROMPT,
                return_tensors="pt"
            ).pixel_values
            output = model.generate(
                pixel_values,
                max_length=256
            )
            text_result = processor.batch_decode(
                output,
                skip_special_tokens=True
            )[0]


            parsed = json.loads(text_result)


            parsed = normalize_fields(parsed)


            results.append(parsed)


        except Exception:

            parsed = hybrid_extract(img)


            parsed = normalize_fields(parsed)


            results.append(parsed)


    return results