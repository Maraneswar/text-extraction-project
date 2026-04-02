/**
 * DocIntel - Intelligent Document Processing
 * Frontend application logic
 */

// ===== State =====
let currentTaskId = null;
let pollInterval = null;

// ===== DOM Elements =====
const $ = (sel) => document.querySelector(sel);
const $$ = (sel) => document.querySelectorAll(sel);

const dropZone = $('#dropZone');
const fileInput = $('#fileInput');
const uploadSection = $('#uploadSection');
const processingSection = $('#processingSection');
const resultsSection = $('#resultsSection');
const toastContainer = $('#toastContainer');
const btnExtractUrl = $('#btnExtractUrl');
const urlInput = $('#urlInput');

// ===== Init =====
document.addEventListener('DOMContentLoaded', () => {
    initUpload();
    initTabs();
    initButtons();
});

// ===== Health Check =====

// ===== Upload =====
function initUpload() {
    // Click to upload
    dropZone.addEventListener('click', () => fileInput.click());

    // File selected
    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handleFile(e.target.files[0]);
        }
    });

    // URL input
    btnExtractUrl.addEventListener('click', () => {
        const url = urlInput.value.trim();
        if (url) {
            handleUrl(url);
        } else {
            showToast('Please enter a valid URL', 'error');
        }
    });

    // Drag and drop
    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.classList.add('drag-over');
    });

    dropZone.addEventListener('dragleave', (e) => {
        e.preventDefault();
        dropZone.classList.remove('drag-over');
    });

    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.classList.remove('drag-over');
        if (e.dataTransfer.files.length > 0) {
            handleFile(e.dataTransfer.files[0]);
        }
    });

    // Format badge filters
    $$('.format-badge').forEach(badge => {
        badge.addEventListener('click', (e) => {
            e.stopPropagation(); // Don't trigger the main dropZone click
            const format = badge.textContent.trim().toLowerCase();
            openFilteredPicker(format);
        });
    });
}

function openFilteredPicker(format) {
    const defaultAccept = fileInput.accept;
    
    // Map of extensions
    const extMap = {
        pdf: '.pdf',
        docx: '.docx',
        png: '.png',
        jpg: '.jpg,.jpeg',
        jpeg: '.jpg,.jpeg',
        tiff: '.tiff',
        bmp: '.bmp',
        webp: '.webp'
    };

    if (extMap[format]) {
        fileInput.accept = extMap[format];
    }

    fileInput.click();

    // Reset accept after a short delay so the main zone works normally
    setTimeout(() => {
        fileInput.accept = defaultAccept;
    }, 500);
}

async function handleFile(file) {
    // Validate extension
    const validExts = ['pdf', 'docx', 'png', 'jpg', 'jpeg', 'tiff', 'bmp', 'webp'];
    const ext = file.name.split('.').pop().toLowerCase();
    if (!validExts.includes(ext)) {
        showToast(`Unsupported file type: .${ext}`, 'error');
        return;
    }

    // Validate size (20MB)
    if (file.size > 20 * 1024 * 1024) {
        showToast('File too large. Maximum size: 20MB', 'error');
        return;
    }

    // Show processing UI
    showSection('processing');
    resetProcessingSteps();

    // Upload
    const formData = new FormData();
    formData.append('file', file);

    try {
        const res = await fetch('/api/upload', {
            method: 'POST',
            body: formData,
        });

        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || 'Upload failed');
        }

        const data = await res.json();
        currentTaskId = data.file_id;

        // Start polling for results
        updateStep('stepExtract', 'active');
        startPolling(data.file_id);

    } catch (e) {
        showToast(e.message || 'Upload failed', 'error');
        showSection('upload');
    }
}

async function handleUrl(url) {
    if (!url.startsWith('http')) {
        showToast('URL must start with http:// or https://', 'error');
        return;
    }

    try {
        resetAll();
        showSection('processing');
        updateStep('stepExtract', 'active');
        
        const response = await fetch('/api/extract/url', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url: url })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to start URL extraction');
        }

        const data = await response.json();
        currentTaskId = data.file_id;
        
        // Polling results
        startPolling(data.file_id);
    } catch (error) {
        showSection('upload');
        showToast(error.message, 'error');
    }
}

// ===== Polling =====
function startPolling(taskId) {
    if (pollInterval) clearInterval(pollInterval);

    pollInterval = setInterval(async () => {
        try {
            const res = await fetch(`/api/status/${taskId}`);
            const data = await res.json();

            if (data.status === 'processing') {
                // Update steps based on available data
                if (data.extraction) {
                    updateStep('stepExtract', 'done');
                    updateStep('stepSummary', 'active');
                }
                if (data.summary) {
                    updateStep('stepSummary', 'done');
                    updateStep('stepEntities', 'active');
                }
                if (data.entities) {
                    updateStep('stepEntities', 'done');
                    updateStep('stepSentiment', 'active');
                }
                if (data.sentiment) {
                    updateStep('stepSentiment', 'done');
                }
            }

            if (data.status === 'completed' || data.status === 'error') {
                clearInterval(pollInterval);
                pollInterval = null;

                // Mark all steps as done
                updateStep('stepExtract', 'done');
                updateStep('stepSummary', 'done');
                updateStep('stepEntities', 'done');
                updateStep('stepSentiment', 'done');

                // Short delay to show completion
                setTimeout(() => {
                    if (data.status === 'error' && !data.extraction) {
                        showToast(data.error_message || 'Processing failed', 'error');
                        showSection('upload');
                    } else {
                        displayResults(data);
                        showSection('results');
                    }
                }, 600);
            }
        } catch (e) {
            clearInterval(pollInterval);
            pollInterval = null;
            showToast('Lost connection to server', 'error');
            showSection('upload');
        }
    }, 800);
}

// ===== Display Results =====
function displayResults(data) {
    // File info bar
    const typeIcons = { pdf: '📕', docx: '📘', image: '🖼️' };
    $('#fileTypeIcon').textContent = typeIcons[data.file_type] || '📄';
    $('#fileName').textContent = data.filename;

    const meta = data.extraction?.metadata;
    const parts = [data.file_type.toUpperCase()];
    if (meta?.word_count) parts.push(`${meta.word_count.toLocaleString()} words`);
    if (meta?.page_count) parts.push(`${meta.page_count} pages`);
    $('#fileMeta').textContent = parts.join(' • ');

    const timeSeconds = (data.processing_time_ms / 1000).toFixed(1);
    $('#processingTime').textContent = `⏱ ${timeSeconds}s`;

    // Extracted Text
    const textEl = $('#extractedText');
    if (data.extraction?.raw_text) {
        textEl.textContent = data.extraction.raw_text;
    } else {
        textEl.innerHTML = `<p class="placeholder">${data.extraction?.error_message || 'No text extracted.'}</p>`;
    }

    // Summary
    if (data.summary) {
        $('#summaryContent').textContent = data.summary.summary;
        $('#summaryStats').classList.remove('hidden');
        $('#statOriginalLen').textContent = data.summary.original_length.toLocaleString();
        $('#statSummaryLen').textContent = data.summary.summary_length.toLocaleString();
        const pct = Math.round((1 - data.summary.compression_ratio) * 100);
        $('#statCompression').textContent = `${pct}%`;
        $('#statAlgorithm').textContent = data.summary.algorithm;
    } else {
        $('#summaryContent').innerHTML = '<p class="placeholder">Summarization not available.</p>';
        $('#summaryStats').classList.add('hidden');
    }

    // Entities
    displayEntities(data.entities);

    // Sentiment
    displaySentiment(data.sentiment);

    // Metadata
    displayMetadata(data.extraction?.metadata);

    // Activate first tab
    activateTab('extracted');
}

function displayEntities(entityData) {
    const catEl = $('#entityCategories');
    const listEl = $('#entityList');
    const countEl = $('#entityCount');

    if (!entityData || entityData.entities.length === 0) {
        catEl.innerHTML = '<p class="placeholder">No entities detected in this document.</p>';
        listEl.innerHTML = '';
        countEl.textContent = '0 entities found';
        return;
    }

    countEl.textContent = `${entityData.total_entities} entities found`;

    // Category badges
    const catColors = {
        PERSON: '#ec4899', ORG: '#3b82f6', GPE: '#10b981', DATE: '#f59e0b',
        MONEY: '#8b5cf6', EVENT: '#06b6d4', PRODUCT: '#fb923c', LAW: '#a855f7',
        NORP: '#f472b6', EMAIL: '#06b6d4', PHONE: '#3b82f6', URL: '#10b981',
        TIME: '#f59e0b', PERCENT: '#8b5cf6', CARDINAL: '#94a3b8',
    };

    catEl.innerHTML = Object.entries(entityData.entity_counts)
        .sort((a, b) => b[1] - a[1])
        .map(([label, count]) => `
            <div class="entity-category-badge">
                <span class="cat-dot" style="background: ${catColors[label] || '#94a3b8'}"></span>
                ${label}
                <span class="cat-count">${count}</span>
            </div>
        `).join('');

    // Entity list
    listEl.innerHTML = entityData.entities
        .slice(0, 100)
        .map(ent => `
            <div class="entity-item">
                <div class="entity-item-left">
                    <span class="entity-type-badge badge-${ent.label}">${ent.label}</span>
                    <span class="entity-text" title="${escapeHtml(ent.text)}">${escapeHtml(ent.text)}</span>
                </div>
                ${ent.count > 1 ? `<span class="entity-item-count">×${ent.count}</span>` : ''}
            </div>
        `).join('');
}

function displaySentiment(sentData) {
    const overviewEl = $('#sentimentOverview');

    if (!sentData) {
        overviewEl.innerHTML = '<p class="placeholder">Sentiment analysis not available.</p>';
        return;
    }

    const score = sentData.overall_compound;
    const label = sentData.overall_label;
    const posW = Math.round(sentData.overall_positive * 100);
    const neuW = Math.round(sentData.overall_neutral * 100);
    const negW = Math.round(sentData.overall_negative * 100);

    // Label color
    let labelColor;
    if (score >= 0.05) labelColor = 'var(--accent-green)';
    else if (score <= -0.05) labelColor = 'var(--accent-red)';
    else labelColor = 'var(--text-muted)';

    let html = `
        <div class="sentiment-gauge-container">
            <div class="sentiment-label-display" style="color: ${labelColor}">${label}</div>
            <div class="sentiment-score">${score >= 0 ? '+' : ''}${score.toFixed(3)}</div>
            <div class="sentiment-bar-container">
                <div class="sentiment-bar">
                    <div class="sentiment-bar-positive" style="width: ${posW}%"></div>
                    <div class="sentiment-bar-neutral" style="width: ${neuW}%"></div>
                    <div class="sentiment-bar-negative" style="width: ${negW}%"></div>
                </div>
                <div class="sentiment-bar-labels">
                    <span><span class="dot dot-pos"></span> Positive ${posW}%</span>
                    <span><span class="dot dot-neu"></span> Neutral ${neuW}%</span>
                    <span><span class="dot dot-neg"></span> Negative ${negW}%</span>
                </div>
            </div>
        </div>
    `;

    // Sentence breakdown
    if (sentData.sentence_breakdown && sentData.sentence_breakdown.length > 0) {
        html += `
            <div class="sentiment-sentences">
                <h4>Sentence-Level Breakdown (top ${Math.min(sentData.sentence_breakdown.length, 20)})</h4>
                ${sentData.sentence_breakdown.slice(0, 20).map(s => {
                    let cls = 'sent-neutral';
                    if (s.compound >= 0.05) cls = 'sent-positive';
                    else if (s.compound <= -0.05) cls = 'sent-negative';
                    return `
                        <div class="sentence-item">
                            <span class="sentence-sentiment-badge ${cls}">${s.label}</span>
                            <span class="sentence-text">${escapeHtml(s.text)}</span>
                        </div>
                    `;
                }).join('')}
            </div>
        `;
    }

    overviewEl.innerHTML = html;
}

function displayMetadata(meta) {
    const metaEl = $('#metadataContent');

    if (!meta) {
        metaEl.innerHTML = '<p class="placeholder">No metadata available.</p>';
        return;
    }

    const rows = [
        ['Title', meta.title],
        ['Author', meta.author],
        ['File Type', meta.file_type],
        ['Page Count', meta.page_count],
        ['Word Count', meta.word_count?.toLocaleString()],
        ['Character Count', meta.character_count?.toLocaleString()],
        ['Created', meta.creation_date],
        ['Modified', meta.modification_date],
    ];

    // Add extra metadata
    if (meta.extra) {
        for (const [key, value] of Object.entries(meta.extra)) {
            if (value && value !== '' && value !== 0 && value !== false) {
                const label = key.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
                rows.push([label, String(value)]);
            }
        }
    }

    metaEl.innerHTML = `
        <table class="metadata-table">
            ${rows.filter(([, v]) => v && v !== 'None' && v !== 'null' && v !== '')
              .map(([k, v]) => `<tr><td>${k}</td><td>${escapeHtml(String(v))}</td></tr>`)
              .join('')}
        </table>
    `;
}

// ===== Tabs =====
function initTabs() {
    $$('.tab').forEach(tab => {
        tab.addEventListener('click', () => {
            activateTab(tab.dataset.tab);
        });
    });
}

function activateTab(tabName) {
    $$('.tab').forEach(t => t.classList.remove('active'));
    $$('.tab-panel').forEach(p => p.classList.remove('active'));

    const tab = $(`.tab[data-tab="${tabName}"]`);
    const panel = $(`#panel${tabName.charAt(0).toUpperCase() + tabName.slice(1)}`);

    if (tab) tab.classList.add('active');
    if (panel) panel.classList.add('active');
}

// ===== Buttons =====
function initButtons() {
    // New upload
    $('#btnNewUpload').addEventListener('click', () => {
        resetAll();
        showSection('upload');
    });

    // Back to upload (without full reset if possible, or just same as New)
    $('#btnBackToUpload').addEventListener('click', () => {
        // We reset anyway for now to avoid data conflicts, 
        // but user specifically asked for "Back"
        resetAll();
        showSection('upload');
    });

    // Cancel processing
    $('#btnCancelProcessing').addEventListener('click', () => {
        if (pollInterval) {
            clearInterval(pollInterval);
            pollInterval = null;
        }
        showSection('upload');
        showToast('Processing cancelled', 'info');
    });

    // Copy buttons
    $('#btnCopyText').addEventListener('click', () => {
        copyToClipboard($('#extractedText').textContent, '#btnCopyText');
    });

    $('#btnCopySummary').addEventListener('click', () => {
        copyToClipboard($('#summaryContent').textContent, '#btnCopySummary');
    });

    // Download button
    $('#btnDownloadText').addEventListener('click', () => {
        if (currentTaskId) {
            window.location.href = `/api/download/${currentTaskId}`;
        } else {
            showToast('No active document to download', 'error');
        }
    });
}

async function copyToClipboard(text, btnSelector) {
    try {
        await navigator.clipboard.writeText(text);
        const btn = $(btnSelector);
        btn.classList.add('copied');
        const originalHTML = btn.innerHTML;
        btn.innerHTML = `<svg width="16" height="16" viewBox="0 0 16 16" fill="none"><path d="M3 8l3 3 7-7" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg> Copied!`;
        setTimeout(() => {
            btn.classList.remove('copied');
            btn.innerHTML = originalHTML;
        }, 2000);
    } catch (e) {
        showToast('Failed to copy to clipboard', 'error');
    }
}

// ===== UI Helpers =====
function showSection(sectionId) {
    [uploadSection, processingSection, resultsSection].forEach(s => s.classList.add('hidden'));
    
    if (sectionId === 'upload') {
        uploadSection.classList.remove('hidden');
    } else if (sectionId === 'processing') {
        processingSection.classList.remove('hidden');
    } else if (sectionId === 'results') {
        resultsSection.classList.remove('hidden');
    }
}
function resetProcessingSteps() {
    ['stepExtract', 'stepSummary', 'stepEntities', 'stepSentiment'].forEach(id => {
        const el = $(`#${id}`);
        el.classList.remove('active', 'done');
        el.querySelector('.step-status').textContent = '⏳';
    });
}

function updateStep(stepId, state) {
    const el = $(`#${stepId}`);
    el.classList.remove('active', 'done');
    el.classList.add(state);
    el.querySelector('.step-status').textContent = state === 'done' ? '✅' : '⚡';
}

function resetAll() {
    currentTaskId = null;
    if (pollInterval) {
        clearInterval(pollInterval);
        pollInterval = null;
    }
    fileInput.value = '';
    $('#extractedText').innerHTML = '<p class="placeholder">No text extracted yet.</p>';
    $('#summaryContent').innerHTML = '<p class="placeholder">No summary available.</p>';
    $('#summaryStats').classList.add('hidden');
    $('#entityCategories').innerHTML = '<p class="placeholder">No entities detected.</p>';
    $('#entityList').innerHTML = '';
    $('#sentimentOverview').innerHTML = '<p class="placeholder">No sentiment data available.</p>';
    $('#metadataContent').innerHTML = '<p class="placeholder">No metadata available.</p>';
}

function showToast(message, type = 'info') {
    const icons = { info: 'ℹ️', error: '❌', success: '✅' };
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `<span class="toast-icon">${icons[type]}</span><span>${escapeHtml(message)}</span>`;
    toastContainer.appendChild(toast);

    setTimeout(() => {
        if (toast.parentNode) toast.remove();
    }, 4000);
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
