# Alldocex — Intelligent Document Processing System

![Version](https://img.shields.io/badge/version-1.1.0-blue)
![License](https://img.shields.io/badge/license-MIT-green)

**Alldocex** is a high-performance, professional-grade document intelligence platform that extracts, analyzes, and summarizes content from various document formats using state-of-the-art AI.

## 🚀 Key Features

*   **Multi-Format Extraction**: Supports PDF, DOCX, and high-resolution images (PNG, JPG, TIFF, etc.).
*   **Gemini AI-Powered Extraction**: Integrates **Gemini 1.5 Flash** for high-precision, layout-aware OCR and structured data extraction.
*   **Structured AI Analysis**:
    *   Generates clean, structured output combining high-level key points and explicitly extracted details (names, phone numbers, contact info).
    *   **Extractive Summarization**: Condenses long documents into bulleted top highlights.
    *   **Named Entity Recognition (NER)** & **Sentiment Analysis**: Detailed semantic NLP via **spaCy** and **VADER**.
*   **Robust Fallback Mechanisms**: Deep scan OCR recovery using **EasyOCR** and **Tesseract** locally when AI processing fails or hits quota limits.
*   **Perfected Document Typography**: Uses **Marked.js** for native Markdown-parsed display delivering mathematically perfect text alignment and human-readable formatting.
*   **Web URL Summarization**: Paste any web link to instantly extract and analyze its core content.
*   **Downloadable & Exportable Results**: Export raw structured summaries and text as clean `.txt` files.
*   **Corporate UI**: A premium Blue & White dashboard with smooth user flows and dynamic interactions.
*   **Cloud Ready**: Specifically tailored and tested for automated deployment to **Hugging Face Spaces**.

## 🛠️ Technology Stack

*   **Backend**: [FastAPI](https://fastapi.tiangolo.com/) (Async Python)
*   **AI Engine**: [Google Gemini API](https://aistudio.google.com/) (Gemini 1.5 Flash)
*   **OCR & Layout Recovery**: [PyMuPDF](https://pymupdf.readthedocs.io/en/latest/), [EasyOCR](https://github.com/JaidedAI/EasyOCR), & [Tesseract](https://github.com/tesseract-ocr/tesseract)
*   **NLP Processing**: [spaCy](https://spacy.io/) & [Sumy](https://github.com/miso-belica/sumy)
*   **Frontend**: Vanilla HTML5, CSS3, ES6 JavaScript, and [Marked.js](https://marked.js.org/) for rendering.

## 📦 Installation & Setup

### 1. Clone the repository
```bash
git clone <your-repo-url>
cd <repo-folder>
```

### 2. Environment Variables
Create a `.env` file in the root directory and add your Google Gemini API key:
```env
GEMINI_API_KEY=your_gemini_api_key_here
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Install NLP model & OS Dependencies (if missing)
```bash
python -m spacy download en_core_web_sm
# Note: Tesseract OCR must be installed on your system's OS layer.
```

## 🏃 Getting Started

1.  Start the backend server:
    ```bash
    python main.py
    ```
2.  Open your browser and navigate to the indicated localhost address (e.g., `http://localhost:7860`).

## 📘 Usage

1.  **Direct Upload**: Drag and drop your PDFs or images into the dashboard.
2.  **Format Selection**: Click on specific badges (PDF, PNG, JPG) to open a filtered file picker.
3.  **URL Entry**: Paste a web link to summarize online articles instantly.
4.  **Download**: Once processing is complete, use the **Download** button to save the extracted text.

---
