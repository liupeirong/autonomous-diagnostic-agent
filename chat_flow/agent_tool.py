import sys
from promptflow import tool
from promptflow.connections import AzureOpenAIConnection
from openai import AzureOpenAI

sys.path.append('../utils')
sys.path.append('../chat')
sys.path.append('../chat/functions')
from chat_function_calling import answer_with_tools


# Since the autonomous agent requires repeated calls to LLM, it's not a DAG (directed acyclic graph)
# that Promptflow is based on. So we create a custom Python tool.
@tool
def pf_agent_tool(aoai_connection: AzureOpenAIConnection, deployment: str, user_question: str, system_message: str, tools: list) -> str:
  aoai = AzureOpenAI(azure_endpoint=aoai_connection.api_base, api_version=aoai_connection.api_version, api_key=aoai_connection.api_key)
  sys_msg = {"role": "system", "content": system_message}
  return answer_with_tools(aoai, deployment, user_question, sys_msg, tools)

