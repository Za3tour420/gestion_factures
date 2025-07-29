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

from core.utils import *
from agent.tools import *

from agent.init_llm import llm

import logging

logger = logging.getLogger(__name__)

# Tools dictionary
registered_tools = [
    init_web_search_tool(),
    get_url_content,
    rag_management_rules,
    rag_usage_cases,
    extract_bofip_updates
]

def build_graph(memory: InMemorySaver):
    # Initialize StateGraph
    workflow = StateGraph(MessagesState)

    # Add nodes
    agent_node = create_react_agent(llm, registered_tools)
    workflow.add_node("agent", agent_node)
    workflow.set_entry_point("agent")
    workflow.set_finish_point("agent")

    # Compile
    return workflow.compile(checkpointer=memory)

# Build graph
logger.info("Starting agent...")
memory = InMemorySaver()
agent_app = build_graph(memory)
logger.info("Agent started!")
        
def user_agent_multiturn(query: str, base64_image: Optional[str] = None, thread_id: str = "1"):
    
    config = {
        "configurable": {"thread_id": thread_id},
        "max_tokens": 32768
    }
    logging.info("Thread ID for conversation: %s", thread_id)

    # Build human message
    human_message = HumanMessage(content=[
        {"type": "text", "text": query},
        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
    ]) if base64_image else HumanMessage(content=query)

    try:
        result = agent_app.invoke({"messages": [human_message]}, config)
        print(result["messages"])
    except Exception as e:
        logging.error(f"Error during agent invocation: {str(e)}", exc_info=True)
        return "Une erreur est survenue lors de la génération de la réponse. Veuillez réessayer."

    # Return only the final AI response
    for msg in reversed(result["messages"]):
        if isinstance(msg, AIMessage):
            return msg.content.strip()

    return "Je n'ai pas pu générer de réponse cette fois."

