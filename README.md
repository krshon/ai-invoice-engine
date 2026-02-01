## AI Invoice Verification System

**Tech:** FastAPI, DONUT OCR, EasyOCR, Async Workers, Job Queue

- Built an asynchronous invoice verification pipeline using FastAPI with
  background workers and a job-queue for non-blocking processing.
- Integrated DONUT Transformer with EasyOCR fallback for field extraction and
  rule-based validation, generating credibility scores and risk labels.
- Implemented live status polling and PDF audit report generation to deliver
  an end-to-end document verification workflow.
