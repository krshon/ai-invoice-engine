from queue_store import job_queue
from invoice_verifier import verify_invoice
import traceback
import requests

HF_OCR_URL = "https://ultrailway-invoice-ocr-service.hf.space/analyze"

def hf_ocr_extract(file_path):
    with open(file_path, "rb") as f:
        response = requests.post(
            HF_OCR_URL,
            files={"file": f},
            timeout=120
        )
    response.raise_for_status()
    return response.json()

def worker_loop(jobs_dict):
    while True:
        job_id = job_queue.get()

        try:
            jobs_dict[job_id]["status"] = "RUNNING"

            extracted = hf_ocr_extract(jobs_dict[job_id]["file_path"])
            jobs_dict[job_id]["extracted"] = extracted

            if not extracted or extracted == []:
                raise ValueError("Extraction returned no results")

            if extracted[0] is None:
                raise ValueError("Empty first page object")

            label, score = verify_invoice(extracted[0])
            jobs_dict[job_id]["verification_score"] = score
            jobs_dict[job_id]["status"] = label

        except Exception as e:
            print("\n🚨 WORKER CRASH DETECTED 🚨")
            traceback.print_exc()
            print("-------------------------------------------------\n")

            jobs_dict[job_id]["retries"] += 1

            if jobs_dict[job_id]["retries"] < jobs_dict[job_id]["max_retries"]:
                jobs_dict[job_id]["status"] = "RETRYING"
                job_queue.put(job_id)
            else:
                jobs_dict[job_id]["status"] = "FAILED"
                jobs_dict[job_id]["error"] = str(e)

        job_queue.task_done()

def start_worker(jobs_dict):
    import threading
    t = threading.Thread(target=worker_loop, args=(jobs_dict,), daemon=True)
    t.start()
