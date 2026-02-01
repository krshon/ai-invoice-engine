from queue_store import job_queue
from donut_model import donut_extract
from invoice_verifier import verify_invoice
import traceback

def worker_loop(jobs_dict):
    while True:
        job_id = job_queue.get()

        try:
            jobs_dict[job_id]["status"] = "RUNNING"

            extracted = donut_extract(jobs_dict[job_id]["file_path"])
            jobs_dict[job_id]["extracted"] = extracted

            # 🛑 If model returns nothing, stop retry
            if not extracted or extracted is None or extracted == []:
                raise ValueError("Extraction returned no results")

            if extracted[0] is None:
                raise ValueError("Empty first page object")

            # Run verification safely
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
