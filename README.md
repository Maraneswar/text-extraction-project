# DocIntel — Intelligent Document Processing System

![Version](https://img.shields.io/badge/version-1.1.0-blue)
![License](https://img.shields.io/badge/license-MIT-green)

**DocIntel** is a high-performance, professional-grade document intelligence platform that extracts, analyzes, and summarizes content from various document formats using state-of-the-art AI.

## 🚀 Key Features

*   **Multi-Format Extraction**: Supports PDF, DOCX, and high-resolution images (PNG, JPG, TIFF, etc.).
*   **Layout-Aware PDF Engine**: Uses advanced 'layout' mode to preserve columns, tables, and physical text positioning.
*   **Intelligent OCR**: Powered by **EasyOCR** (Deep Learning based) for superior accuracy in scanned documents.
*   **Web URL Summarization**: Paste any web link to instantly extract and analyze its core content.
*   **AI Analysis Suite**:
    *   **Extractive Summarization**: Condenses long documents into key highlights.
    *   **Named Entity Recognition (NER)**: Detects People, Organizations, Dates, and more via **spaCy**.
    *   **Sentiment Analysis**: Analyzes emotional tone using the **VADER** algorithm.
*   **Downloadable Results**: Export extracted text as clean `.txt` files.
*   **Corporate UI**: A professional Blue & White dashboard with smooth animations and intuitive navigation.

## 🛠️ Technology Stack

*   **Backend**: [FastAPI](https://fastapi.tiangolo.com/) (Async Python)
*   **PDF Processing**: [PyMuPDF](https://pymupdf.readthedocs.io/en/latest/) (Layout Mode)
*   **OCR**: [EasyOCR](https://github.com/JaidedAI/EasyOCR) & [Tesseract](https://github.com/tesseract-ocr/tesseract)
*   **NLP**: [spaCy](https://spacy.io/) & [Sumy](https://github.com/miso-belica/sumy)
*   **Frontend**: Vanilla HTML5, CSS3 (Modern UI), and JavaScript (ES6+)

## 📦 Installation

### 1. Clone the repository
```bash
git clone <your-repo-url>
cd guvi-extraction
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Install NLP model
```bash
python -m spacy download en_core_web_sm
```

## 🏃 Getting Started

1.  Start the backend server:
    ```bash
    python main.py
    ```
2.  Open your browser and navigate to:
    `http://localhost:8000`

## 📘 Usage

1.  **Direct Upload**: Drag and drop your PDFs or images into the dashboard.
2.  **Format Selection**: Click on specific badges (PDF, PNG, JPG) to open a filtered file picker.
3.  **URL Entry**: Paste a web link to summarize online articles instantly.
4.  **Download**: Once processing is complete, use the **Download** button to save the extracted text.

---

*Developed with ❤️ for Intelligent Document Analysis.*
