"""
Web content extraction from URLs using requests and BeautifulSoup4.
Extracts title and main text content from HTML pages.
"""
import time
import requests
from bs4 import BeautifulSoup
from models.schemas import ExtractionResult, DocumentMetadata


def extract_url(url: str) -> ExtractionResult:
    """Fetch and extract text content from a web URL."""
    start_time = time.time()

    try:
        # 1. Fetch content
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        # 2. Parse HTML
        soup = BeautifulSoup(response.text, 'html.parser')

        # 3. Remove script and style elements
        for script_or_style in soup(["script", "style", "nav", "footer", "header", "aside"]):
            script_or_style.decompose()

        # 4. Get text
        # Try to find the title
        title = soup.title.string.strip() if soup.title else url

        # Get main text - simple heuristic: look for <article> or just <body>
        content_area = soup.find('article') or soup.body
        if not content_area:
             content_area = soup

        # Extract text while preserving some paragraph structure
        lines = []
        for element in content_area.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'li']):
            text = element.get_text().strip()
            if text:
                if element.name.startswith('h'):
                    prefix = '#' * int(element.name[1])
                    lines.append(f"\n{prefix} {text}\n")
                else:
                    lines.append(text)

        full_text = "\n\n".join(lines)
        if not full_text.strip():
            # Fallback to general text extraction
            full_text = soup.get_text(separator='\n\n', strip=True)

        # 5. Build metadata
        metadata = DocumentMetadata(
            title=title,
            author="Web Content",
            creation_date="",
            modification_date="",
            page_count=None,
            word_count=len(full_text.split()),
            character_count=len(full_text),
            file_type="URL",
            extra={
                "url": url,
                "domain": url.split('/')[2] if '//' in url else url.split('/')[0],
                "status_code": response.status_code,
                "content_type": response.headers.get('Content-Type', '')
            }
        )

        elapsed = (time.time() - start_time) * 1000

        if not full_text.strip():
            return ExtractionResult(
                raw_text="",
                metadata=metadata,
                success=False,
                error_message="Could not extract any meaningful text from the provided URL.",
                extraction_time_ms=elapsed,
            )

        return ExtractionResult(
            raw_text=full_text,
            metadata=metadata,
            success=True,
            extraction_time_ms=elapsed,
        )

    except requests.exceptions.RequestException as e:
        elapsed = (time.time() - start_time) * 1000
        return ExtractionResult(
            raw_text="",
            metadata=DocumentMetadata(file_type="URL", extra={"url": url}),
            success=False,
            error_message=f"Failed to fetch URL: {str(e)}",
            extraction_time_ms=elapsed,
        )
    except Exception as e:
        elapsed = (time.time() - start_time) * 1000
        return ExtractionResult(
            raw_text="",
            metadata=DocumentMetadata(file_type="URL", extra={"url": url}),
            success=False,
            error_message=f"Web extraction failed: {str(e)}",
            extraction_time_ms=elapsed,
        )
