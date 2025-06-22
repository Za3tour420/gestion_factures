from langchain_core.messages import HumanMessage
from langchain_nvidia_ai_endpoints import ChatNVIDIA
from utils import encode_image, get_api_key

def create_multimodal_prompt(query: str, image_path: str) -> list:
    encoded_image = encode_image(image_path)

    if image_path.lower().endswith('.png'):
        mime_type = 'image/png'
    elif image_path.lower().endswith(('.jpg', '.jpeg')):
        mime_type = 'image/jpeg'
    else:
        raise ValueError("Unsupported image type. Use PNG or JPG.")

    return [
        HumanMessage(
            content=[
                {"type": "text", "text": query},
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:{mime_type};base64,{encoded_image}"},
                },
            ]
        )
    ]


llm = ChatNVIDIA(
    base_url="https://integrate.api.nvidia.com/v1",
    model="mistralai/mistral-medium-3-instruct",
    api_key=get_api_key(),
    temperature=0
)

# Change query and image here
query = "Extraire tous les articles de cette facture."
image_path = "test3.jpg"

messages = create_multimodal_prompt(query, image_path)
result = llm.invoke(messages)

print(result.content)

