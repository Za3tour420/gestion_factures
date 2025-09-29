# agentic.py

from typing import Annotated, Optional, List, Any, Dict
from typing_extensions import TypedDict

from langchain_core.messages import HumanMessage, AIMessage
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
    summarize_url_content,
    rag_management_rules,
    rag_usage_cases,
    extract_products_and_services,
    save_to_excel,
    sandbox_tool
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
        
async def user_agent_multiturn(query: str, processed_files: Optional[List[Dict[str, Any]]] = None, thread_id: str = "1", messages_to_invoke: Optional[List] = None):
    
    config = {
        "configurable": {"thread_id": thread_id},
        "max_tokens": 32768
    }
    logging.info("Thread ID for conversation: %s", thread_id)
    
    try:
        result = await agent_app.ainvoke({"messages": messages_to_invoke}, config)
        print(result)
        
        # Log the conversation for debugging
        logger.info("Agent response generated successfully")
            
    except Exception as e:
        logging.error(f"Error during agent invocation: {str(e)}", exc_info=True)
        
        # Provide more specific error messages based on the type of error
        if "token" in str(e).lower():
            return "La requête contient trop de données. Veuillez réduire le nombre de fichiers ou leur taille."
        elif "timeout" in str(e).lower():
            return "La requête a pris trop de temps à traiter. Veuillez réessayer avec moins de fichiers."
        else:
            return "Une erreur est survenue lors de la génération de la réponse. Veuillez réessayer."
    
    # Return only the final AI response
    for msg in reversed(result["messages"]):
        if isinstance(msg, AIMessage):
            response_content = msg.content.strip()
            
            # Add file processing summary if multiple files were processed
            """if processed_files and len(processed_files) > 1:
                file_count_summary = f"\n\n📊 *Résumé: {len(processed_files)} fichiers analysés*"
                response_content = response_content + file_count_summary"""
                
            return response_content
            
    return "Je n'ai pas pu générer de réponse cette fois."
