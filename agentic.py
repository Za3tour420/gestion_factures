from typing import Annotated, Optional
from typing_extensions import TypedDict

import base64


from langchain_core.messages import HumanMessage, AIMessage, ToolMessage, FunctionMessage
from langchain_core.tools import tool
from langchain_nvidia_ai_endpoints import ChatNVIDIA

from langgraph.prebuilt import create_react_agent, ToolNode, tools_condition
from langgraph.graph import StateGraph, START, END, MessagesState
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver

from utils import *
from tools import *

# Instantiate the model
llm = ChatNVIDIA(
    base_url="https://integrate.api.nvidia.com/v1",
    model="mistralai/mistral-small-3.1-24b-instruct-2503",
    api_key=get_mistral_small_api_key(),
    temperature=0
)

# Tools init
web_search_tool = init_web_search_tool()

# Tools dictionary
tools = [web_search_tool]

# Initialize StateGraph
workflow = StateGraph(MessagesState)

# Add nodes
agent_node = create_react_agent(llm, tools)
workflow.add_node("agent", agent_node)
workflow.set_entry_point("agent")
workflow.set_finish_point("agent")

# Memory
memory = MemorySaver()

# Compile
app = workflow.compile(checkpointer=memory)

print(app.get_graph().draw_ascii())

config = {"configurable": {"thread_id": "1"}}
        
def user_agent_multiturn(query: str, base64_image: Optional[str] = None):
    print(f"User: {query}")
    
    # Build query with image if provided
    content = [{"type": "text", "text": query}]
    if base64_image:
        content.append({
            "type": "image_url",
            "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}})
    message = HumanMessage(content=content)
    
    result = app.invoke({"messages": [message]}, config)

    # Print assistant's final reply
    print("Agent:", end=" ")
    for msg in result["messages"]:
        if isinstance(msg, AIMessage):
            print(msg.content)

    # Print tool call and response if it happened
    for msg in result["messages"]:
        if isinstance(msg, ToolMessage) or isinstance(msg, FunctionMessage):
            print(f"[TOOL CALLED] Tool name: {msg.name}, Output: {msg.content}")
    print("\n")

base64_image = pdf_page_to_base64("test_interface/exemple de facture/reexempledefacture/FACTURE_H0771_BIL_613334_958061.PDF", 1)

query = """
Tu es un expert en analyse de factures.

Analyse l'image suivante puis:
1. Extrait tous les articles avec leur description, prix unitaire, quantité, code TVA appliqué, montant total (HT et/ou TTC) et toute autre donnée utile.
2. Vérifie pour chaque article si le taux de TVA appliqué est correct ou non.
3. Si 'arrh client' ou une dénomination similaire est présente au sein des articles, ça représente la somme d'argent déposée par le client au fournisseur des biens et/ou services.

Indique clairement les erreurs éventuelles, et propose les taux attendus le cas échéant.
Présente le tout sous forme de tableau clair.
"""
user_agent_multiturn(query, base64_image)
