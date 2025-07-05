import os, base64
import io

import fitz
from PIL import Image

def get_nim_api_key():
    return os.environ.get("NVIDIA_API_MISTRAL_MEDIUM3_INSTRUCT") # mistralai/mistral-medium-3-instruct
def get_mistral_small_api_key():
    return os.environ.get("NVIDIA_API_MISTRAL_SMALL31_INSTRUCT") # mistralai/mistral-small-3.1-24b-instruct-2503
def get_tavily_api_key():
    return os.environ.get("TAVILY_API_KEY")
def get_google_api_keys():
    return os.environ.get("GOOGLE_API_KEY"), os.environ.get("GOOGLE_CSE_ID")
    
def encode_image(image_path: str):
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode('utf-8')

def encode_pdf(pdf_path: str):
    all_pages_b64 = []
    
    try:
        with fitz.open(pdf_path) as doc:
            for page_num in range(doc.page_count):
                page = doc.load_page(page_num)
                pix = page.get_pixmap()
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

                buffer = io.BytesIO()
                img.save(buffer, format="PNG")
                all_pages_b64.append(base64.b64encode(buffer.getvalue()).decode("utf-8"))
    except Exception as e:
        print(f"An error occured: {e}")

    return all_pages_b64
    
