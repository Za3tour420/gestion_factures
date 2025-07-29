from langchain_nvidia_ai_endpoints import ChatNVIDIA

from core.utils import get_mistral_small_api_key

# Instantiate the model
llm = ChatNVIDIA(
    base_url="https://integrate.api.nvidia.com/v1",
    model="mistralai/mistral-small-3.1-24b-instruct-2503",
    api_key=get_mistral_small_api_key(),
    temperature=0
)
