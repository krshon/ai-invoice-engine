from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import uuid, os
from fastapi.staticfiles import StaticFiles


from worker import start_worker
from queue_store import job_queue
from cache import status_cache
from report_generator import generate_invoice_report

app = FastAPI(title="Invoice OCR & Verification Engine")
app.mount("/frontend", StaticFiles(directory="frontend"), name="frontend")


# --------- 🌐 ENABLE CORS for Frontend ---------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # allow all for local dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------- 📄 FRONTEND ROUTE ---------
@app.get("/")
def frontend():
    return FileResponse("frontend/index.html")

# --------- 🗂 JOB STORAGE ---------
jobs = {}
UPLOAD_DIR = "invoices"
os.makedirs(UPLOAD_DIR, exist_ok=True)


# --------- 🛠 WORKER STARTUP ---------
@app.on_event("startup")
def startup_event():
    start_worker(jobs)


# --------- 📌 UPLOAD INVOICE ---------
@app.post("/upload-invoice")
async def upload_invoice(file: UploadFile = File(...)):
    job_id = str(uuid.uuid4())
    file_path = f"{UPLOAD_DIR}/{job_id}_{file.filename}"

    # Save file to disk
    with open(file_path, "wb") as f:
        f.write(await file.read())

    # Register job
    jobs[job_id] = {
        "job_id": job_id,
        "file_path": file_path,
        "status": "PENDING",
        "retries": 0,
        "max_retries": 3,
        "verification_score": None,
        "extracted": None
    }

    # Queue job
    job_queue.put(job_id)

    return {
        "job_id": job_id,
        "message": "Invoice received. Processing started.",
        "status": "PENDING"
    }


# --------- 📍 CHECK STATUS + DOWNLOAD PDF ---------
@app.get("/invoice-status/{job_id}")
def invoice_status(job_id: str, download: bool = False):

    job = jobs.get(job_id)

    if not job:
        return {"status": "NOT_FOUND"}

    # 📄 Generate PDF if requested
    if download:
        if job["status"] != "completed":
            return {"error": "Result not ready yet"}

        os.makedirs("reports", exist_ok=True)
        output_path = f"reports/{job_id}.pdf"

        extracted_data = job.get("extracted", {})
        extracted_data["verification_score"] = job.get("verification_score")
        extracted_data["label"] = job.get("label")

        generate_invoice_report(job_id, extracted_data, output_path)

        return {
            "status": "completed",
            "download_path": output_path
        }

    # ✅ STOP polling once job completes
    if job["status"] == "completed":
        return {
            "status": "completed",
            "label": job.get("label"),
            "score": job.get("verification_score"),
            "signals": job.get("signals"),
            "extracted": job.get("extracted")
        }

    # otherwise still processing
    return {
        "status": job["status"]
    }