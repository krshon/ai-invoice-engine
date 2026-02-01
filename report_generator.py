from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from datetime import datetime

def generate_invoice_report(job_id, data, output_path):
    c = canvas.Canvas(output_path, pagesize=A4)
    width, height = A4

    c.setFont("Helvetica-Bold", 18)
    c.drawString(50, height - 50, "AI Invoice Verification System")

    c.setFont("Helvetica", 12)
    c.drawString(50, height - 90, f"Job ID: {job_id}")
    c.drawString(50, height - 110, f"Vendor: {data.get('vendor', 'N/A')}")
    c.drawString(50, height - 130, f"Detected Total: {data.get('total', 'N/A')}")
    c.drawString(50, height - 150, f"Verification Score: {data.get('verification_score', 'N/A')}")
    c.drawString(50, height - 170, f"Status: {data.get('status', 'N/A')}")

    c.drawString(50, height - 210, "Extracted OCR Text:")
    c.setFont("Helvetica", 10)
    text = c.beginText(50, height - 230)
    text.textLines(data.get("raw_text", "No OCR text found"))
    c.drawText(text)

    c.setFont("Helvetica", 10)
    c.drawString(50, 50, f"Generated on: {datetime.now().strftime('%d %b %Y, %I:%M %p')}")

    c.save()
    return output_path
