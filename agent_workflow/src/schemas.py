from langgraph.graph import MessagesState
from typing_extensions import TypedDict


class StateInput(TypedDict):
    # This is the input to the state
    url: str


class State(MessagesState):
    # We can add a specific key to our state for the user input
    url: str
