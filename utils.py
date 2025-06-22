import os, base64

def encode_image(image_path: str):
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode('utf-8')
def get_api_key():
    return os.environ.get("NVIDIA_API_MISTRAL_MEDIUM3_INSTRUCT")
