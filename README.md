# AI Invoice Verification Pipeline (OCR + Fraud Detection + FastAPI)

An asynchronous AI-powered invoice verification system that extracts structured invoice data using OCR models and detects fraud signals through rule-based validation and anomaly scoring.

The system processes invoices concurrently using background workers and generates explainable risk reports to assist automated document verification workflows.

🔗 **Live Demo:** *(ai-invoice-engine.onrender.com/)*  
📂 **Sample Invoices:** `/samples` folder inside repo


---

# Key Features

- Hybrid OCR extraction using **DONUT OCR + EasyOCR**
- LLM-assisted structured data validation
- Async processing pipeline using **FastAPI background workers**
- Fraud detection engine with explainable risk scoring
- Template reuse detection
- Arithmetic inconsistency detection
- Vendor anomaly detection
- Automated verification report generation
- Concurrent processing support for multiple invoices


---

# System Architecture
Upload Invoice
↓
FastAPI Server
↓
Task Queue / Background Worker
↓
DONUT OCR + EasyOCR Extraction
↓
LLM Field Validation
↓
Fraud Detection Engine
↓
Risk Score + Report Generator
↓
Verification Output


# Performance

- Successfully processed **100+ invoices**
- Supports concurrent execution using async workers
- Reduces manual verification effort through automated fraud scoring
# Future Improvements

- Vendor history database integration
- Signature detection module
- GST validation API integration
- Layout similarity detection using embeddings
- Confidence calibration dashboard


---

# Project Motivation

Manual invoice verification is slow, error-prone, and difficult to scale.  
This system automates extraction and fraud detection using OCR + NLP techniques while providing interpretable verification scores for decision support.

