import sys
from promptflow import tool


sys.path.append('../utils')
sys.path.append('../chat/functions')
sys.path.append('../chat')
from chat_function_calling import tools

# Promptflow tools are not the same as OpenAI tools.
# This is a Promptflow tool to define the tools the LLM could call.
@tool
def pf_llm_tools() -> list:
  return tools
