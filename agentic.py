from typing import Annotated
from typing_extensions import TypedDict

from langchain_core.messages import HumanMessage, AIMessage, ToolMessage, FunctionMessage
from langchain_core.tools import tool
from langchain_nvidia_ai_endpoints import ChatNVIDIA

from langgraph.prebuilt import create_react_agent, ToolNode, tools_condition
from langgraph.graph import StateGraph, START, END, MessagesState
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver

from utils import *
from tools import init_web_search_tool

# Instantiate the model
llm = ChatNVIDIA(
    base_url="https://integrate.api.nvidia.com/v1",
    model="mistralai/mistral-medium-3-instruct",
    api_key=get_nim_api_key(),
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

"""def user_agent_multiturn(queries):
    for query in queries:
        print(f"User: {query}")
        print("Agent: ", end="")
        for msg, _ in app.stream(
            {"messages": [HumanMessage(content=query)]},
            config,
            stream_mode="messages"
        ):
            if hasattr(msg, "content") and msg.content:
                print(msg.content, end="", flush=True)
        print("\n")"""
        
def user_agent_multiturn(queries):
    for query in queries:
        print(f"\nUser: {query}")
        result = app.invoke({"messages": [HumanMessage(content=query)]}, config)

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

queries = ["Quel est le taux de TVA de base en France?", "Quel taux serait appliqué pour l'achat d'un laptop à 500 euros?", "Chercher tous les taux appliqués en France."]
user_agent_multiturn(queries)
