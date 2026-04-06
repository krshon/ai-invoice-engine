// Invoice Verification System - JavaScript (REAL BACKEND VERSION)

// DOM Elements
const uploadSection = document.getElementById('uploadSection');
const resultsSection = document.getElementById('resultsSection');
const uploadArea = document.getElementById('uploadArea');
const fileInput = document.getElementById('fileInput');
const browseBtn = document.getElementById('browseBtn');
const newVerificationBtn = document.getElementById('newVerificationBtn');
const verificationStatus = document.getElementById('verificationStatus');
const scoreCard = document.getElementById('scoreCard');
const documentAnalysis = document.getElementById('documentAnalysis');
const riskIndicators = document.getElementById('riskIndicators');
const explanationCard = document.getElementById('explanationCard');
const downloadBtn = document.getElementById('downloadBtn');
const downloadJsonBtn = document.getElementById('downloadJsonBtn');

let currentResultData = null;
let currentJobId = null;


// ================= EVENTS =================

browseBtn.addEventListener('click', () => fileInput.click());
fileInput.addEventListener('change', handleFileSelect);
newVerificationBtn.addEventListener('click', resetVerification);
downloadBtn.addEventListener('click', downloadBackendPDF);
downloadJsonBtn.addEventListener('click', downloadJSONData);


// ================= DRAG & DROP =================

uploadArea.addEventListener('dragover', (e) => {
    e.preventDefault();
    uploadArea.classList.add('drag-over');
});

uploadArea.addEventListener('dragleave', () => {
    uploadArea.classList.remove('drag-over');
});

uploadArea.addEventListener('drop', (e) => {
    e.preventDefault();
    uploadArea.classList.remove('drag-over');

    const files = e.dataTransfer.files;
    if (files.length > 0) handleFile(files[0]);
});


// ================= FILE HANDLING =================

function handleFileSelect(e) {
    const file = e.target.files[0];
    if (file) handleFile(file);
}

function handleFile(file) {

    const validTypes = ['application/pdf', 'image/jpeg', 'image/png', 'image/jpg'];

    if (!validTypes.includes(file.type)) {
        alert('Upload PDF, JPG, or PNG only');
        return;
    }

    if (file.size > 10 * 1024 * 1024) {
        alert('File must be < 10MB');
        return;
    }

    processInvoice(file);
}


// ================= MAIN BACKEND PIPELINE =================

async function processInvoice(file) {

    const formData = new FormData();
    formData.append("file", file);

    try {

        const response = await fetch("/upload-invoice", {
            method: "POST",
            body: formData
        });

        const data = await response.json();

        console.log("UPLOAD RESPONSE JOB ID:", data.job_id);

        currentJobId = data.job_id;

        pollStatus(currentJobId);

    } catch (err) {
        alert("Upload failed");
        console.error(err);
    }
}


// ================= POLLING WORKER STATUS =================
let pollingInterval = null;

function pollStatus(jobId) {

    console.log("POLLING JOB ID:", jobId);

    if (pollingInterval) {
        clearInterval(pollingInterval);
    }

    pollingInterval = setInterval(async () => {

        try {

            const res = await fetch(`/invoice-status/${jobId}`);
            const job = await res.json();

            console.log("STATUS:", job.status);

            if (job.status === "NOT_FOUND") {
                clearInterval(pollingInterval);
                pollingInterval = null;

                alert("Session expired. Please upload again.");
                return;
            }

            if (job.status === "completed") {

                clearInterval(pollingInterval);
                pollingInterval = null;

                console.log("DISPLAYING RESULTS NOW");

                displayResults(convertBackendResult(job));

                return;
            }

        } catch (err) {

            console.error("Polling error:", err);
            clearInterval(pollingInterval);
        }

    }, 1000);
}

function convertBackendResult(job) {

        console.log("Signals received:", job.signals);
    const extracted = job.extracted ?? {};
    const signals = job.signals || {};

    let analysis = [];
    let risks = [];

    // Positive signal if required fields exist
    if (!signals.missing_fields?.length) {
        analysis.push({
            type: "pass",
            title: "Required Fields Present",
            text: "Vendor and total detected successfully"
        });
    }

    // Format warnings (example: vendor_detected_as_logo)
    if (signals.format_warnings?.length) {
        signals.format_warnings.forEach(flag => {
            risks.push({
                type: "warning",
                title: "Format Warning",
                text: flag.replaceAll("_", " ")
            });
        });
    }

    // Confidence flags (example: invoice_no_missing)
    if (signals.confidence_flags?.length) {
        signals.confidence_flags.forEach(flag => {
            risks.push({
                type: "fail",
                title: "Fraud Indicator",
                text: flag.replaceAll("_", " ")
            });
        });
    }

    // Missing required fields
    if (signals.missing_fields?.length) {
        signals.missing_fields.forEach(field => {
            risks.push({
                type: "fail",
                title: "Missing Field",
                text: `${field} not detected`
            });
        });
    }

    // Map backend label → UI style
    let uiStatus = "fraudulent";

    if (job.label === "LIKELY LEGIT") uiStatus = "authentic";
    if (job.label === "NEEDS REVIEW") uiStatus = "suspicious";
    if (job.label === "SUSPICIOUS") uiStatus = "fraudulent";
    if (job.label === "NOT AN INVOICE") uiStatus = "fraudulent";

    return {
        status: uiStatus,
        score: job.score ?? job.verification_score ?? 0,
        analysis,
        risks,
explanation: {
    title: "Why this invoice received this result",

    content:
        job.signals?.summary ||
        `Model classified invoice as: ${job.status}`,

    details:
        job.signals?.reasons?.length
            ? job.signals.reasons
            : [
                extracted.vendor
                    ? `Vendor detected: ${extracted.vendor}`
                    : "Vendor missing",

                extracted.total
                    ? `Invoice total detected: ${extracted.total}`
                    : "Invoice total missing",

                extracted.invoice_no
                    ? `Invoice number detected: ${extracted.invoice_no}`
                    : "Invoice number missing"
            ],

    recommendation:
        job.status === "LIKELY LEGIT"
            ? "Invoice structure appears consistent."
            : "Manual verification recommended before approval."
},

        extracted: extracted,

};
}// ================= DISPLAY RESULTS =================



function getItemIcon(type) {
    return {
        pass: "✓",
        warning: "⚠",
        fail: "✗"
    }[type] || "•";
}
function displayResults(result) {

    console.log("DISPLAY RESULTS CALLED");

    console.log("DISPLAY RESULTS CALLED", result);

    // ================= DOCUMENT ANALYSIS =================

documentAnalysis.innerHTML = (result.analysis || []).map(item => `
    <div class="detail-item ${item.type}">
        <div class="detail-item-icon">${getItemIcon(item.type)}</div>
        <div class="detail-item-content">
            <div class="detail-item-title">${item.title}</div>
            <div class="detail-item-text">${item.text}</div>
        </div>
    </div>
`).join('');


// ================= RISK INDICATORS =================

riskIndicators.innerHTML = (result.risks || []).map(item => `
    <div class="detail-item ${item.type}">
        <div class="detail-item-icon">${getItemIcon(item.type)}</div>
        <div class="detail-item-content">
            <div class="detail-item-title">${item.title}</div>
            <div class="detail-item-text">${item.text}</div>
        </div>
    </div>
`).join('');

    currentResultData = result;

    uploadSection.classList.add('hidden');
    resultsSection.classList.remove('hidden');

    const statusConfig = {
        authentic: { class: 'status-authentic', icon: '✓', text: 'Invoice Verified — Appears Authentic' },
        suspicious: { class: 'status-suspicious', icon: '⚠', text: 'Suspicious — Requires Manual Review' },
        fraudulent: { class: 'status-fraudulent', icon: '✗', text: 'High Risk — Likely Fraudulent' }
    };

    const config = statusConfig[result.status];

    verificationStatus.className = `verification-status ${config.class}`;
    verificationStatus.innerHTML = `
        <div class="status-icon">${config.icon}</div>
        <div>${config.text}</div>
    `;

    scoreCard.className = `score-card score-${result.status}`;
    scoreCard.innerHTML = `
        <div>
            <div class="score-label">Verification Score</div>
            <div class="score-value">${result.score}<span style="font-size:20px;opacity:0.4;">/100</span></div>
        </div>
        <div class="score-bar-wrap">
            <div class="score-description">${getScoreDescription(result.score)}</div>
            <div class="score-bar-track">
                <div class="score-bar-fill" style="width:${result.score}%"></div>
            </div>
        </div>
    `;

explanationCard.innerHTML = `
    <h3>${result.explanation.title}</h3>

    <p>${result.explanation.content}</p>

    ${
        result.explanation.details?.length
        ? `
        <ul style="margin-top:12px;">
            ${result.explanation.details
                .map(d => `<li>${d}</li>`)
                .join("")}
        </ul>
        `
        : ""
    }

    <p style="margin-top:14px;">
        <strong>Recommendation:</strong>
        ${result.explanation.recommendation}
    </p>
`;
}


// ================= SCORE DESCRIPTION =================

function getScoreDescription(score) {

    if (score >= 85) return 'High confidence — invoice appears authentic';
    if (score >= 70) return 'Moderate confidence — some concerns detected';
    if (score >= 50) return 'Low confidence — multiple red flags present';

    return 'Very low confidence — likely fraudulent';
}


// ================= RESET =================

function resetVerification() {

    resultsSection.classList.add('hidden');
    uploadSection.classList.remove('hidden');

    fileInput.value = '';
    currentResultData = null;
}


// ================= DOWNLOAD BACKEND PDF =================

async function downloadBackendPDF() {

    if (!currentJobId) return;

    const res = await fetch(`/invoice-status/${currentJobId}?download=true`);
    const data = await res.json();

    if (!data.download_path) {
        alert("Report not ready yet");
        return;
    }

    window.open(`/${data.download_path}`, "_blank");
}


// ================= SAMPLE BUTTON SUPPORT =================

document.querySelectorAll(".btn-sample").forEach(button => {

    button.addEventListener("click", async () => {

        const filename = button.dataset.file;

        const response = await fetch(`/frontend/examples/${filename}`);
        const blob = await response.blob();

        const file = new File([blob], filename);

        handleFile(file);
    });
});


// ================= DOWNLOAD JSON =================

function downloadJSONData() {

    if (!currentResultData) return;

    const blob = new Blob(
        [JSON.stringify(currentResultData, null, 2)],
        { type: 'application/json' }
    );

    const url = URL.createObjectURL(blob);

    const a = document.createElement('a');
    a.href = url;
    a.download = `invoice-verification-data-${Date.now()}.json`;

    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);

    URL.revokeObjectURL(url);
}