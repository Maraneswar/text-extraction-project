# Alldocex - Deployment Guide

This guide provides three main options for deploying the Alldocex application to a production environment.

## 🏗️ Option 1: Docker (Recommended)

Docker is the best choice because it packages all the AI models, dependencies, and system libraries into a single container.

### 1. Build the image
```bash
docker build -t alldocex-app .
```

### 2. Run with Docker Compose
```bash
docker-compose up -d
```
The application will be available at `http://localhost:8000`.

---

## ☁️ Option 2: Cloud Deployment (Render / Railway / Fly.io)

### **Render Deployment (Recommended)**
1.  **Connect GitHub**: Push your code to a GitHub repository.
2.  **Create Web Service**: Select "Web Service" in Render.
3.  **Docker Environment**: Render will automatically detect the `Dockerfile`.
4.  **Resource Plan**: Ensure you select a plan with at least **4GB RAM** (e.g., Starter or Pro).
5.  **Environment Variables**: Add `PORT = 8000` if required.

---

## 🖥️ Option 3: Manual Deployment (Ubuntu/Debian Server)

If you are deploying directly to a Linux VPS (without Docker):

### 1. Install System Dependencies
```bash
sudo apt-get update
sudo apt-get install -y tesseract-ocr libgl1-mesa-glx libglib2.0-0 build-essential python3-venv
```

### 2. Set Up Environment
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

### 3. Run with Gunicorn (Production Server)
```bash
pip install gunicorn
gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app --bind 0.0.0.0:8000
```

---

## ⚠️ Important Considerations

*   **RAM**: AI models (EasyOCR, Torch, spaCy) are memory-intensive. Do NOT deploy on a "Free Tier" instance with only 512MB or 1GB of RAM.
*   **Disk Space**: The first time you run the app, it will download several hundred megabytes of model weights.
*   **Permissions**: Ensure the `uploads/` directory has write permissions for the user running the application.
*   **Reverse Proxy**: For public deployment, it is highly recommended to use **Nginx** as a reverse proxy with SSL (Let's Encrypt).
