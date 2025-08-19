import os, base64
import io

import fitz
from PIL import Image

from dotenv import load_dotenv

# Load env variables
load_dotenv()

MAX_RESOLUTION = 768

def get_mistral_small_api_key():
    key = os.getenv("NVIDIA_API_MISTRAL_SMALL31_INSTRUCT") # mistralai/mistral-small-3.1-24b-instruct-2503
    if not key:
        raise EnvironmentError("Missing NVIDIA_API_MISTRAL_SMALL31_INSTRUCT in environment.")
    return key

def get_google_api_keys():
    google_key = os.getenv("GOOGLE_API_KEY")
    cse_id = os.getenv("GOOGLE_CSE_ID")
    if not google_key or not cse_id:
        raise EnvironmentError("Missing GOOGLE_API_KEY or GOOGLE_CSE_ID in environment.")
    return google_key, cse_id
    
def resize_image(img: Image.Image, max_size: int = MAX_RESOLUTION) -> Image.Image:
    if img.width > max_size or img.height > max_size:
        img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
    return img
    
def encode_image(image_path: str):
    with Image.open(image_path) as img:
        img = resize_image(img)
        
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        return base64.b64encode(buffer.getvalue()).decode('utf-8')

def encode_image_bytes(image_bytes: bytes):
    try:
        with Image.open(io.BytesIO(image_bytes)) as img:
            img = resize_image(img)
            
            buffer = io.BytesIO()
            img.save(buffer, format="PNG")
            return base64.b64encode(buffer.getvalue()).decode('utf-8')
    except Exception as e:
        print(f"An error occurred encoding image from bytes: {e}")
        return None

def encode_pdf(pdf_path: str):
    b64_page = None
    try:
        with fitz.open(pdf_path) as doc:
            page = doc.load_page(0)
            pix = page.get_pixmap()
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

            buffer = io.BytesIO()
            img.save(buffer, format="PNG")
            b64_page = base64.b64encode(buffer.getvalue()).decode("utf-8")
    except Exception as e:
        print(f"An error occured: {e}")

    return b64_page

def encode_pdf_from_stream(file_stream):
    b64_page = None
    try:
        with fitz.open(stream=file_stream, filetype="pdf") as doc:
            page = doc.load_page(0)
            pix = page.get_pixmap()
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            
            img = resize_image(img)

            buffer = io.BytesIO()
            img.save(buffer, format="PNG")
            b64_page = base64.b64encode(buffer.getvalue()).decode("utf-8")
    except Exception as e:
        print(f"An error occurred: {e}")

    return b64_page

    
