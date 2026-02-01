import fitz  # PyMuPDF
from PIL import Image, ImageEnhance
from transformers import DonutProcessor, VisionEncoderDecoderModel
import io, json, re
import easyocr  # NEW

# Load DONUT model
MODEL_NAME = "naver-clova-ix/donut-base-finetuned-docvqa"
processor = DonutProcessor.from_pretrained(MODEL_NAME)
model = VisionEncoderDecoderModel.from_pretrained(MODEL_NAME)

# Load EasyOCR for fallback
reader = easyocr.Reader(['en'], gpu=False)

TASK_PROMPT = "<s>invoice information extraction</s>"

# -------------------------
# Image Preprocessing
# -------------------------
def preprocess_image(img):
    img = img.convert("RGB")
    img = img.resize((1280, 1280))  # upscale for clarity
    img = ImageEnhance.Contrast(img).enhance(1.5)
    img = ImageEnhance.Sharpness(img).enhance(1.3)
    return img

# -------------------------
# EasyOCR fallback extraction
# -------------------------
def hybrid_extract(img):
    import numpy as np
    img_np = np.array(img)  # Convert PIL image to numpy array for EasyOCR

    # EasyOCR text extraction
    text_lines = reader.readtext(img_np, detail=False)
    raw_text = "\n".join(text_lines)

    # 🔧 Normalize formatting for numbers (European comma → decimal)
    clean_text = raw_text.replace(",", ".").replace(" ", "")

    # 🎯 Extract total amount (more flexible regex)
    amount = re.search(r'\$?\d{2,8}\.\d{2}', clean_text)

    # 🎯 Vendor extraction (ignore 'INVOICE' text and uppercase cleanup)
    vendor = None
    vendor_candidates = [line for line in raw_text.split("\n") if len(line.strip()) > 2]
    for v in vendor_candidates:
        if "invoice" not in v.lower():
            vendor = v.strip()
            break

    return {
        "raw_text": raw_text,
        "total": amount.group(0) if amount else None,
        "vendor": vendor if vendor else None
    }



# -------------------------
# Main extraction function
# -------------------------
def donut_extract(file_path):
    images = []

    # If PDF, convert pages to images
    if file_path.lower().endswith(".pdf"):
        pdf = fitz.open(file_path)
        for page in pdf:
            pix = page.get_pixmap()
            img = Image.open(io.BytesIO(pix.tobytes("png")))
            images.append(preprocess_image(img))
        pdf.close()

    # If image file
    else:
        img = Image.open(file_path)
        images.append(preprocess_image(img))

    results = []

    # Process each page/image
    for img in images:
        try:
            pixel_values = processor(img, TASK_PROMPT, return_tensors="pt").pixel_values
            output = model.generate(pixel_values, max_length=256)
            text_result = processor.batch_decode(output, skip_special_tokens=True)[0]

            parsed = json.loads(text_result)  # try JSON output
            results.append(parsed)

        except Exception:
            # 🔥 FIX: CORRECT INDENT + ALWAYS RETURN A LIST
            parsed = hybrid_extract(img)
            results.append(parsed)  # <-- add to list, do NOT exit early

    return results  # <-- ALWAYS RETURN A LIST
