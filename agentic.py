import json
from typing import Annotated
from typing_extensions import TypedDict

from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.tools import tool
from langchain_tavily import TavilySearch
from langchain_nvidia_ai_endpoints import ChatNVIDIA

from langgraph.prebuilt import create_react_agent, ToolNode, tools_condition
from langgraph.graph import StateGraph, START, END, MessagesState
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver

from utils import *

# Instantiate the model
llm = ChatNVIDIA(
    base_url="https://integrate.api.nvidia.com/v1",
    model="mistralai/mistral-medium-3-instruct",
    api_key=get_nim_api_key(),
    temperature=0
)

# Tools
web_search = TavilySearch(
            max_results = 1,
            include_answer=True,
)

tools = [web_search]

# State for graph
class State(TypedDict):
    messages: Annotated[list, add_messages]

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

def user_agent_multiturn(queries):
    for query in queries:
        print(f"User: {query}")
        print("Agent: ", end="")
        for msg, _ in app.stream(
            {"messages": [HumanMessage(content=query)]},
            config,
            stream_mode="messages"
        ):
            if hasattr(msg, "content") and msg.content:
                content = msg.content
                try:
                    data = json.loads(content)
                    if isinstance(data, dict) and "answer" in data:
                        print(data["answer"], end="", flush=True)
                    else:
                        # Fallback: print raw if it's not Tavily-style JSON
                        print(content, end="", flush=True)
                except json.JSONDecodeError:
                    # Not JSON, just print it
                    print(content, end="", flush=True)
        print("\n")

queries = ["Quel est le taux de TVA de base en France?", "Chercher tous les taux appliqués."]
user_agent_multiturn(queries)
