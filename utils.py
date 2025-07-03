import os, base64
import io

import fitz
from PIL import Image

def encode_image(image_path: str):
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode('utf-8')
def get_nim_api_key():
    return os.environ.get("NVIDIA_API_MISTRAL_MEDIUM3_INSTRUCT") # mistralai/mistral-medium-3-instruct
def get_mistral_small_api_key():
    return os.environ.get("NVIDIA_API_MISTRAL_SMALL31_INSTRUCT") # mistralai/mistral-small-3.1-24b-instruct-2503
def get_tavily_api_key():
    return os.environ.get("TAVILY_API_KEY")
def get_google_api_keys():
    return os.environ.get("GOOGLE_API_KEY"), os.environ.get("GOOGLE_CSE_ID")
def pdf_page_to_base64(pdf_path: str, page_number: int):
    pdf_document = fitz.open(pdf_path)
    page = pdf_document.load_page(page_number - 1)  # input is one-indexed
    pix = page.get_pixmap()
    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

    buffer = io.BytesIO()
    img.save(buffer, format="PNG")

    return base64.b64encode(buffer.getvalue()).decode("utf-8")
