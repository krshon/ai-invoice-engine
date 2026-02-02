// Invoice Verification System - JavaScript

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

// Store current result data
let currentResultData = null;

// Event Listeners
browseBtn.addEventListener('click', () => fileInput.click());
fileInput.addEventListener('change', handleFileSelect);
newVerificationBtn.addEventListener('click', resetVerification);
downloadBtn.addEventListener('click', downloadPDFReport);
downloadJsonBtn.addEventListener('click', downloadJSONData);

// Drag and Drop Events
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
    if (files.length > 0) {
        handleFile(files[0]);
    }
});

// File Handling
function handleFileSelect(e) {
    const file = e.target.files[0];
    if (file) {
        handleFile(file);
    }
}

function handleFile(file) {
    // Validate file type
    const validTypes = ['application/pdf', 'image/jpeg', 'image/png', 'image/jpg'];
    if (!validTypes.includes(file.type)) {
        alert('Please upload a valid file (PDF, JPG, or PNG)');
        return;
    }

    // Validate file size (10MB)
    if (file.size > 10 * 1024 * 1024) {
        alert('File size must be less than 10MB');
        return;
    }

    // Simulate processing
    processInvoice(file);
}

// Main Processing Function
function processInvoice(file) {
    // Simulate AI processing delay
    setTimeout(() => {
        // Generate random verification result for demo
        const verificationResult = generateVerificationResult(file.name);
        displayResults(verificationResult);
    }, 1500);
}

// Generate Verification Result (Simulated AI Analysis)
function generateVerificationResult(fileName) {
    // Random result for demo purposes
    const random = Math.random();
    let status, score, analysis, risks, explanation, extracted;

    if (random > 0.6) {
        // Authentic Invoice
        status = 'authentic';
        score = Math.floor(Math.random() * 15) + 85; // 85-100
        extracted = {
            invoice_number: 'INV-2024-' + Math.floor(Math.random() * 10000),
            date: '2024-01-15',
            vendor: 'Acme Corporation Ltd.',
            total_amount: '$' + (Math.random() * 10000 + 1000).toFixed(2),
            tax_id: 'TX' + Math.floor(Math.random() * 1000000),
            items_count: Math.floor(Math.random() * 10) + 1
        };
        analysis = [
            { type: 'pass', title: 'Document Structure', text: 'Standard invoice format detected with proper headers and sections' },
            { type: 'pass', title: 'Company Information', text: 'Valid company registration number and tax ID verified' },
            { type: 'pass', title: 'Font Consistency', text: 'Consistent font usage throughout the document' },
            { type: 'pass', title: 'Sequential Numbering', text: 'Invoice number follows logical sequence pattern' }
        ];
        risks = [
            { type: 'pass', title: 'No Alterations Detected', text: 'Document shows no signs of digital manipulation' },
            { type: 'pass', title: 'Metadata Intact', text: 'Creation metadata matches claimed invoice date' },
            { type: 'pass', title: 'Logo Quality', text: 'Company logo is high-resolution and authentic' }
        ];
        explanation = {
            title: 'Verification Result: Likely Authentic',
            content: `This invoice appears to be legitimate based on our comprehensive analysis. All critical verification checks have passed successfully.`,
            details: [
                'The document structure follows standard business invoice formatting',
                'Company registration details have been cross-verified',
                'No digital manipulation or editing artifacts were detected',
                'Metadata and creation timestamps are consistent',
                'All numerical data (totals, taxes) calculate correctly'
            ],
            recommendation: 'This invoice shows strong indicators of authenticity. However, for high-value transactions, we recommend additional verification through direct contact with the issuing company.'
        };
    } else if (random > 0.3) {
        // Suspicious Invoice
        status = 'suspicious';
        score = Math.floor(Math.random() * 25) + 50; // 50-75
        extracted = {
            invoice_number: 'INV-2024-' + Math.floor(Math.random() * 10000),
            date: '2024-01-15',
            vendor: 'Unknown Vendor Inc.',
            total_amount: '$' + (Math.random() * 10000 + 1000).toFixed(2),
            tax_id: 'UNVERIFIED',
            items_count: Math.floor(Math.random() * 10) + 1,
            warnings: ['Metadata inconsistency', 'Non-standard formatting']
        };
        analysis = [
            { type: 'warning', title: 'Document Structure', text: 'Non-standard layout detected for claimed company type' },
            { type: 'pass', title: 'Company Information', text: 'Company details are present but could not be verified' },
            { type: 'warning', title: 'Font Inconsistency', text: 'Multiple fonts detected, unusual for professional invoices' },
            { type: 'fail', title: 'Sequential Numbering', text: 'Invoice number pattern is irregular' }
        ];
        risks = [
            { type: 'warning', title: 'Minor Alterations', text: 'Possible text editing detected in amount fields' },
            { type: 'warning', title: 'Metadata Concerns', text: 'Document creation date differs from invoice date by 45+ days' },
            { type: 'pass', title: 'Logo Quality', text: 'Logo resolution is acceptable' }
        ];
        explanation = {
            title: 'Why This Invoice May Be Fake',
            content: `Our AI system has identified several red flags that suggest this invoice may not be authentic. These indicators warrant careful review before processing.`,
            details: [
                '<strong>Font Inconsistency:</strong> The invoice uses multiple different fonts, which is uncommon in legitimate business documents generated from accounting software',
                '<strong>Irregular Invoice Numbering:</strong> The invoice number does not follow typical sequential patterns, suggesting manual creation rather than system-generated',
                '<strong>Metadata Mismatch:</strong> The document creation date is significantly later than the invoice date, which may indicate backdating',
                '<strong>Template Inconsistency:</strong> The layout does not match standard templates used by the claimed company',
                '<strong>Calculation Anomalies:</strong> Minor discrepancies in tax calculations or totals may indicate manual editing'
            ],
            recommendation: 'We recommend additional verification steps: Contact the company directly using independently verified contact information (not from the invoice), request a copy from their records, verify the referenced purchase order or contract, and check if the payment details match the company\'s registered banking information.'
        };
    } else {
        // Fraudulent Invoice
        status = 'fraudulent';
        score = Math.floor(Math.random() * 30) + 10; // 10-40
        extracted = {
            invoice_number: 'FAKE-' + Math.floor(Math.random() * 10000),
            date: 'INVALID',
            vendor: 'FRAUDULENT ENTITY',
            total_amount: 'MANIPULATED',
            tax_id: 'INVALID',
            items_count: 0,
            errors: ['Multiple critical failures', 'Document manipulation detected', 'Invalid company data']
        };
        analysis = [
            { type: 'fail', title: 'Document Structure', text: 'Poor quality PDF with embedded image rather than text' },
            { type: 'fail', title: 'Company Information', text: 'Company registration number is invalid or non-existent' },
            { type: 'fail', title: 'Font Quality', text: 'Pixelated text indicates screenshot or image conversion' },
            { type: 'fail', title: 'Sequential Numbering', text: 'Duplicate invoice number found in database' }
        ];
        risks = [
            { type: 'fail', title: 'Digital Manipulation', text: 'Clear evidence of photoshopping or content replacement' },
            { type: 'fail', title: 'Metadata Red Flags', text: 'Metadata has been stripped or falsified' },
            { type: 'fail', title: 'Logo Mismatch', text: 'Company logo differs from official branding' },
            { type: 'fail', title: 'Banking Details', text: 'Bank account does not match company registration country' }
        ];
        explanation = {
            title: 'Critical Alert: Likely Fraudulent Invoice',
            content: `This invoice exhibits multiple severe indicators of fraud. Our AI system has detected manipulation, falsified information, and other red flags that strongly suggest this is a fraudulent document.`,
            details: [
                '<strong>Document Manipulation:</strong> Clear evidence of digital editing using image manipulation software. Text layers show signs of being added after document creation',
                '<strong>Invalid Company Details:</strong> The company registration number does not exist in official business registries, or belongs to a different company entirely',
                '<strong>Poor Document Quality:</strong> The invoice appears to be a screenshot or image rather than a properly generated PDF, suggesting it was created using basic editing tools',
                '<strong>Duplicate Invoice Number:</strong> This exact invoice number has been flagged in our fraud database or appears in previous submissions',
                '<strong>Banking Information Mismatch:</strong> The bank account details do not align with the claimed company location or verified banking information',
                '<strong>Template Anomalies:</strong> The invoice template shows characteristics of freely available fake invoice generators',
                '<strong>Calculation Errors:</strong> Mathematical errors in totals, taxes, or line items that would not occur in legitimate accounting software'
            ],
            recommendation: 'DO NOT PROCESS THIS INVOICE. This document should be treated as fraudulent. Recommended actions: Immediately flag this invoice in your system, do not make any payments to the listed bank account, report this to your security team and potentially law enforcement, contact the claimed company through official channels to verify they did not issue this invoice, preserve all communication related to this invoice for investigation purposes.'
        };
    }

    return { status, score, analysis, risks, explanation, extracted, fileName };
}

// Display Results
function displayResults(result) {
    // Store result data for downloads
    currentResultData = result;

    // Hide upload section
    uploadSection.classList.add('hidden');
    
    // Show results section
    resultsSection.classList.remove('hidden');

    // Set verification status
    const statusConfig = {
        authentic: {
            class: 'status-authentic',
            icon: '✓',
            text: 'Invoice Verified - Appears Authentic'
        },
        suspicious: {
            class: 'status-suspicious',
            icon: '⚠',
            text: 'Suspicious - Requires Manual Review'
        },
        fraudulent: {
            class: 'status-fraudulent',
            icon: '✗',
            text: 'High Risk - Likely Fraudulent'
        }
    };

    const config = statusConfig[result.status];
    verificationStatus.className = `verification-status ${config.class}`;
    verificationStatus.innerHTML = `
        <div class="status-icon">${config.icon}</div>
        <div>${config.text}</div>
    `;

    // Display verification score
    scoreCard.className = `score-card score-${result.status}`;
    scoreCard.innerHTML = `
        <div class="score-label">Verification Score</div>
        <div class="score-value">${result.score}/100</div>
        <div class="score-description">${getScoreDescription(result.score)}</div>
    `;

    // Populate document analysis
    documentAnalysis.innerHTML = result.analysis.map(item => `
        <div class="detail-item ${item.type}">
            <div class="detail-item-icon">${getItemIcon(item.type)}</div>
            <div class="detail-item-content">
                <div class="detail-item-title">${item.title}</div>
                <div class="detail-item-text">${item.text}</div>
            </div>
        </div>
    `).join('');

    // Populate risk indicators
    riskIndicators.innerHTML = result.risks.map(item => `
        <div class="detail-item ${item.type}">
            <div class="detail-item-icon">${getItemIcon(item.type)}</div>
            <div class="detail-item-content">
                <div class="detail-item-title">${item.title}</div>
                <div class="detail-item-text">${item.text}</div>
            </div>
        </div>
    `).join('');

    // Populate explanation
    explanationCard.innerHTML = `
        <h3>${result.explanation.title}</h3>
        <p><strong>${result.explanation.content}</strong></p>
        <p><strong>Key Findings:</strong></p>
        <ul>
            ${result.explanation.details.map(detail => `<li>${detail}</li>`).join('')}
        </ul>
        <p style="margin-top: 20px;"><strong>Recommendation:</strong> ${result.explanation.recommendation}</p>
        ${result.extracted ? `
            <p style="margin-top: 20px;"><strong>Extracted Data:</strong></p>
            <pre style="background: white; border: 1px solid var(--neutral-200); padding: 16px; border-radius: 8px; font-size: 13px;">${JSON.stringify(result.extracted, null, 2)}</pre>
        ` : ''}
    `;
}

// Get score description
function getScoreDescription(score) {
    if (score >= 85) return 'High confidence - Invoice appears authentic';
    if (score >= 70) return 'Moderate confidence - Some concerns detected';
    if (score >= 50) return 'Low confidence - Multiple red flags present';
    return 'Very low confidence - Likely fraudulent';
}

// Helper function for icons
function getItemIcon(type) {
    const icons = {
        pass: '✓',
        fail: '✗',
        warning: '⚠'
    };
    return icons[type] || '•';
}

// Reset Verification
function resetVerification() {
    resultsSection.classList.add('hidden');
    uploadSection.classList.remove('hidden');
    fileInput.value = '';
    currentResultData = null;
}

// Download PDF Report
function downloadPDFReport() {
    if (!currentResultData) return;

    // Create a simple text-based report (in a real app, this would generate a proper PDF)
    const reportContent = `
INVOICE VERIFICATION REPORT
===========================

File: ${currentResultData.fileName}
Date: ${new Date().toLocaleString()}
Status: ${currentResultData.status.toUpperCase()}
Verification Score: ${currentResultData.score}/100

ANALYSIS SUMMARY:
${currentResultData.analysis.map(a => `- ${a.title}: ${a.text}`).join('\n')}

RISK INDICATORS:
${currentResultData.risks.map(r => `- ${r.title}: ${r.text}`).join('\n')}

EXPLANATION:
${currentResultData.explanation.title}
${currentResultData.explanation.content}

Key Findings:
${currentResultData.explanation.details.map(d => `- ${d.replace(/<[^>]*>/g, '')}`).join('\n')}

Recommendation:
${currentResultData.explanation.recommendation}

${currentResultData.extracted ? `
EXTRACTED DATA:
${JSON.stringify(currentResultData.extracted, null, 2)}
` : ''}

---
Report generated by AI Invoice Verification System
    `.trim();

    // Create and download
    const blob = new Blob([reportContent], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `invoice-verification-report-${Date.now()}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

// Download JSON Data
function downloadJSONData() {
    if (!currentResultData) return;

    const jsonData = JSON.stringify(currentResultData, null, 2);
    const blob = new Blob([jsonData], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `invoice-verification-data-${Date.now()}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}