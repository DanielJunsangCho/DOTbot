from prompts.agent_prompt import agent_system_prompt
from prompts.tools_prompts import URL_TOOLS_PROMPT, CSV_TOOLS_PROMPT

from tools.csv_utils import write_to_csv
from tools.langgraph_utils import Done
from tools.webscrape_utils import url_handler

from schemas import State, StateInput
from typing import Literal
from langchain.chat_models import init_chat_model
from langgraph.graph import StateGraph, START, END
from langchain_core.messages import HumanMessage

from dotenv import load_dotenv
load_dotenv("../../.env")

# from ... import config

# Collect all tools
tools = [url_handler, write_to_csv, Done]
tools_by_name = {tool.name: tool for tool in tools}
background = None

llm = init_chat_model("openai:gpt-4-turbo", temperature=0.0)
llm_with_tools = llm.bind_tools(tools, tool_choice="any")

def llm_call(state: State):
    """LLM decides whether to call a tool or not"""

    return {
        "messages": [
            # Invoke the LLM
            llm_with_tools.invoke(
                # Add the system prompt
                [   
                    {"role": "system", "content": agent_system_prompt.format(
                        url=state['url'],
                        url_tools_prompt=URL_TOOLS_PROMPT,
                        csv_tools_prompt=CSV_TOOLS_PROMPT,
                        background=background,
                    )
                }
                ]
                # Add the current messages to the prompt
                + state["messages"]
            )
        ]
    }

def tool_handler(state: State):
    """Performs the tool call."""

    # List for tool messages
    result = []
    
    # Iterate through tool calls
    for tool_call in state["messages"][-1].tool_calls:
        # Get the tool
        tool = tools_by_name[tool_call["name"]]
        # Run it
        observation = tool.invoke(tool_call["args"])
        # Create a tool message
        result.append({"role": "tool", "content" : observation, "tool_call_id": tool_call["id"]})
    
    # Add it to our messages
    return {"messages": result}

def should_continue(state: State) -> Literal["tool_handler", "__end__"]:
    """Route to tool handler, or end if Done tool called."""
    
    # Get the last message
    messages = state["messages"]
    last_message = messages[-1]
    
    # Check if it's a Done tool call
    if last_message.tool_calls:
        for tool_call in last_message.tool_calls: 
            if tool_call["name"] == "Done":
                return "__end__"
            else:
                return "tool_handler"
                
    return "__end__" 


# Build workflow
overall_workflow = StateGraph(State)

# Add nodes
overall_workflow.add_node("llm_call", llm_call)
overall_workflow.add_node("tool_handler", tool_handler)

# Add edges
overall_workflow.add_edge(START, "llm_call")
overall_workflow.add_conditional_edges(
    "llm_call",
    should_continue,
    {
        "tool_handler": "tool_handler",
        "__end__": END,
    },
)
overall_workflow.add_edge("tool_handler", "llm_call")

# Compile the agent
agent = overall_workflow.compile()

response = agent.invoke({"url": "https://www.tradingview.com/markets/stocks-usa/earnings/", 
                        "messages": [HumanMessage(content="Find me all stocks and their related info")]})

