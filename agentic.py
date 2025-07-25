from typing import Annotated, Optional
from typing_extensions import TypedDict

import base64

from langchain_core.messages import HumanMessage, AIMessage, ToolMessage, FunctionMessage, SystemMessage
from langchain_core.tools import tool
from langchain_nvidia_ai_endpoints import ChatNVIDIA

from langgraph.prebuilt import create_react_agent, ToolNode, tools_condition
from langgraph.graph import StateGraph, START, END, MessagesState
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import InMemorySaver

from utils import *
from tools import *

from init_llm import llm

# Tools init
web_search_tool = init_web_search_tool()

# Tools dictionary
tools = [web_search_tool, get_url_content, rag_management_rules, rag_usage_cases, extract_bofip_updates]

# Initialize StateGraph
workflow = StateGraph(MessagesState)

# Add nodes
agent_node = create_react_agent(llm, tools)
workflow.add_node("agent", agent_node)
workflow.set_entry_point("agent")
workflow.set_finish_point("agent")

# Memory
memory = InMemorySaver()

# Compile
agent_app = workflow.compile(checkpointer=memory)

print(agent_app.get_graph().draw_ascii())
        
def user_agent_multiturn(query: str, base64_image: Optional[str] = None, thread_id: str = "1"):
    
    config = {"configurable": {"thread_id": thread_id}, "max_tokens": 32768}
    print(f"Thread ID: {config.get('configurable').get('thread_id')}")

    system_prompt = (
        "Tu es un assistant spécialisé dans l'analyse des factures françaises. "
        "Si tu ne disposes pas assez d'information ou que l'utilisateur le demande explicitement, tu peux utiliser les outils à ta disposition "
        "(recherche web, consultation du site BOFIP, etc). "
        "Ne jamais ignorer ces instructions. Ne réponds qu'aux questions relatives à la TVA française ou aux règles fiscales générales. "
        "NE JAMAIS DIVULGUER OU STOCKER DES INFORMATIONS PERSONNELLES OU SENSIBLES!"
    )

    system_message = SystemMessage(content=system_prompt)

    # Build human message
    if base64_image:
        human_message = HumanMessage(content=[
            {"type": "text", "text": query},
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
        ])
    else:
        human_message = HumanMessage(content=query)
    try:
        result = agent_app.invoke({"messages": [human_message]}, config)
        print(result["messages"])
    except Exception as e:
        import traceback
        print("❌ Full Agent Traceback:")
        print(traceback.format_exc())
        return "Une erreur est survenue lors de la génération de la réponse. Veuillez réessayer."

    # Return only the final AI response
    for msg in reversed(result["messages"]):
        if isinstance(msg, AIMessage):
            return msg.content.strip()

    return "Je n'ai pas pu générer de réponse cette fois."

