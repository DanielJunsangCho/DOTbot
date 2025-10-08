from pydantic import BaseModel
from langchain_core.tools import tool

@tool
class Done(BaseModel):
      """E-mail has been sent."""
      done: bool
