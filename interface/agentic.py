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
agent_app = workflow.compile(checkpointer=memory)

print(agent_app.get_graph().draw_ascii())
        
def user_agent_multiturn(query: str, base64_image: Optional[str] = None, thread_id: str = "1"):
    print(f"User: {query}")
    
    config = {"configurable":  {"thread_id": thread_id}}
    # Build query with image if provided
    content = [{"type": "text", "text": query}]
    if base64_image:
        content.append({
            "type": "image_url",
            "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}})
    message = HumanMessage(content=content)
    
    result = agent_app.invoke({"messages": [message]}, config)

    response_text = ""
    for msg in result["messages"]:
        if isinstance(msg, AIMessage):
            response_text += msg.content + "\n"
        elif isinstance(msg, ToolMessage) or isinstance(msg, FunctionMessage):
            response_text += f"\n[TOOL] {msg.name}: {msg.content}\n"

    return response_text.strip()
