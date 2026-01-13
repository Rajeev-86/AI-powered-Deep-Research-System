import trafilatura
from concurrent.futures import ThreadPoolExecutor, TimeoutError
import logging
import requests
from io import BytesIO
import pypdf
import pdfplumber

logging.basicConfig(level=logging.INFO)


def _is_pdf_url(url):
    """Check if URL points to a PDF file."""
    return url.lower().endswith('.pdf') or '.pdf?' in url.lower()


def _scrape_pdf(url, timeout=15):
    """
    Extract text from PDF URL.
    Uses pypdf for simple PDFs, falls back to pdfplumber for complex ones.
    """
    try:
        # Download PDF with streaming to handle large files better
        response = requests.get(
            url, 
            timeout=timeout, 
            stream=True,
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        )
        
        if response.status_code != 200:
            logging.warning(f"PDF download failed with status {response.status_code}")
            return None
        
        # Check content type
        content_type = response.headers.get('content-type', '').lower()
        if 'pdf' not in content_type and not url.endswith('.pdf'):
            logging.warning(f"URL doesn't appear to be a PDF: {content_type}")
            return None
        
        # Read content in chunks to avoid memory issues
        pdf_content = BytesIO()
        chunk_size = 8192
        total_size = 0
        max_size = 50 * 1024 * 1024  # 50MB limit
        
        for chunk in response.iter_content(chunk_size=chunk_size):
            if chunk:
                total_size += len(chunk)
                if total_size > max_size:
                    logging.warning(f"PDF too large (>{max_size/1024/1024}MB), truncating")
                    break
                pdf_content.write(chunk)
        
        pdf_content.seek(0)
        text_content = []
        
        # Try pypdf first (faster, works for most PDFs)
        try:
            reader = pypdf.PdfReader(pdf_content)
            
            # Limit to first 30 pages for performance (most relevant info is usually early)
            max_pages = min(len(reader.pages), 30)
            
            for page_num in range(max_pages):
                page = reader.pages[page_num]
                text = page.extract_text()
                if text and text.strip():
                    text_content.append(text)
            
            if text_content:
                full_text = "\n\n".join(text_content)
                # Basic cleanup
                full_text = full_text.replace('\x00', '')  # Remove null bytes
                full_text = full_text.replace('\ufffd', '')  # Remove replacement chars
                return full_text
        
        except Exception as pypdf_error:
            logging.info(f"pypdf failed, trying pdfplumber: {str(pypdf_error)[:50]}")
            
            # Fallback to pdfplumber (better for complex layouts)
            try:
                pdf_content.seek(0)  # Reset file pointer
                with pdfplumber.open(pdf_content) as pdf:
                    max_pages = min(len(pdf.pages), 30)
                    
                    for page_num in range(max_pages):
                        page = pdf.pages[page_num]
                        text = page.extract_text()
                        if text and text.strip():
                            text_content.append(text)
                
                if text_content:
                    return "\n\n".join(text_content)
            
            except Exception as plumber_error:
                logging.error(f"Both PDF parsers failed: {str(plumber_error)[:50]}")
                return None
        
        return None
        
    except requests.exceptions.Timeout:
        logging.warning(f"PDF download timeout")
        return None
    except requests.exceptions.RequestException as e:
        logging.error(f"PDF download error: {str(e)[:50]}")
        return None
    except Exception as e:
        logging.error(f"PDF parsing error: {str(e)[:50]}")
        return None


def _scrape_worker(url):
    """
    Main scraping worker. Routes to appropriate parser based on URL type.
    """
    try:
        # Check if it's a PDF
        if _is_pdf_url(url):
            return _scrape_pdf(url, timeout=15)
        
        # Regular HTML scraping with trafilatura
        downloaded = trafilatura.fetch_url(url)

        if downloaded is None:
            return None
        
        text = trafilatura.extract(
            downloaded,
            include_comments=False,      # LLMs don't need user comments
            include_tables=False,        # Tables often break tokenization
            no_fallback=True,            # Faster, but might miss some complex layouts
            include_images=False         # We only want text
        )

        return text
    except Exception as e:
        return None
    
def scrape_with_timeout(url, timeout=5):
    """
    Scrape content from URL with timeout.
    Automatically adjusts timeout for PDFs (they take longer to download/parse).
    """
    # PDFs need more time for download + parsing
    if _is_pdf_url(url):
        timeout = max(timeout * 3, 20)  # At least 20 seconds for PDFs

    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(_scrape_worker, url)

        try:
            result = future.result(timeout=timeout)
            return result
        
        except TimeoutError:
            logging.warning(f"Timeout reached for {url}. Skipping.")
            return None
        except Exception as e:
            logging.error(f"Scraping error for {url}: {e}")
            return None
        
'''
# --- TEST ZONE ---
if __name__ == "__main__":
    # Let's test it on a real article (using a Wikipedia link as example)
    test_url = "https://en.wikipedia.org/wiki/Artificial_intelligence"
    
    print(f"Scraping: {test_url} (Timeout: 5s)...")
    content = scrape_with_timeout(test_url, timeout=5)
    
    if content:
        print("\nSUCCESS! Extracted Content Preview:")
        print("-" * 40)
        print(content[:500] + "...") # Print first 500 chars
        print("-" * 40)
    else:
        print("\nFailed to extract content.")
'''