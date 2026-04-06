from queue_store import job_queue
from invoice_verifier import verify_invoice
from donut_model import donut_extract
from gemini_extractor import gemini_extract
import traceback


def worker_loop(jobs_dict):

    while True:

        print("Worker waiting for job...")
        job_id = job_queue.get()
        print("Worker received job:", job_id)

        try:

            job = jobs_dict[job_id]

            print("Processing job:", job_id)

            job["status"] = "RUNNING"


            # ================= GEMINI EXTRACTION =================

            try:

                gemini_data = gemini_extract(job["file_path"])

                print("Gemini extraction result:", gemini_data)

                extracted = {
                    "vendor": gemini_data.get("vendor"),
                    "invoice_no": gemini_data.get("invoice_no"),
                    "date": gemini_data.get("date"),
                    "total": gemini_data.get("total"),
                    "subtotal": gemini_data.get("subtotal"),
                    "tax": gemini_data.get("tax"),
                    "vendor_gst": gemini_data.get("vendor_gst"),
                    "raw_text": str(gemini_data),
                    "summary": gemini_data.get("summary", ""),
                    "reasons": gemini_data.get("reasons", [])
                }

                job["extracted"] = extracted

                job["signals"] = {
                    "missing_fields": gemini_data.get("missing_fields", []),
                    "format_warnings": gemini_data.get("format_warnings", []),
                    "confidence_flags": gemini_data.get("confidence_flags", []),
                    "summary": gemini_data.get("summary"),
                    "reasons": gemini_data.get("reasons", [])
                }

                print("✅ Gemini extraction complete")


            except Exception as e:

                print("❌ Gemini extraction error:", e)
                print("Falling back to DONUT...")

                extracted_list = donut_extract(job["file_path"])

                if not extracted_list:
                    raise ValueError("Fallback extraction failed")

                extracted = extracted_list[0]

                job["extracted"] = extracted

                fallback_result = verify_invoice(extracted)

                job["signals"] = fallback_result["signals"]

                print("✅ DONUT fallback extraction complete")


            # ================= FINAL VERIFICATION =================

            verification_input = job.get("extracted", {})
            
            result = verify_invoice(verification_input)
            print("Verification result:", result)
            
            gemini_signals = job.get("signals", {})
            job["verification_score"] = result.get("score", 0)
            job["label"] = result.get("label", "UNKNOWN")
            
            merged_signals = result.get("signals", {})
            
            if gemini_signals.get("summary"):
                merged_signals["summary"] = gemini_signals["summary"]
                
            if gemini_signals.get("reasons"):
                merged_signals["reasons"] = gemini_signals["reasons"]
                
                job["signals"] = merged_signals
                job["extracted"] = verification_input
                job["status"] = "completed"
        except Exception as e:

            print("\n🚨 WORKER ERROR 🚨")
            traceback.print_exc()
            print("--------------------------------------\n")

            job = jobs_dict[job_id]

            job["retries"] += 1

            if job["retries"] < job["max_retries"]:

                job["status"] = "RETRYING"
                print("Retrying job:", job_id)

                job_queue.put(job_id)

            else:

                job["status"] = "FAILED"
                job["verification_score"] = 0
                job["error"] = str(e)

                print("Job failed permanently:", job_id)


        finally:

            job_queue.task_done()


def start_worker(jobs_dict):

    import threading

    worker_thread = threading.Thread(
        target=worker_loop,
        args=(jobs_dict,),
        daemon=True
    )

    worker_thread.start()