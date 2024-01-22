import sys
from langchain.chat_models import AzureChatOpenAI

from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.tools import  tool
from langchain_core.messages import HumanMessage, SystemMessage

sys.path.append('./utils')
from loadenv import LLMConfig
sys.path.append('./chat/functions')
from robot_general import get_robots, search_robot_manuals


@tool("search_robot_manuals")
def search_robot_manuals_tool(query: str, kind: str = None) -> str:
  """Search the robot manuals for robot faults, troubleshooting guides, development API etc."""
  return search_robot_manuals(query, kind)


@tool("get_robots")
def get_robots_tool(name: str = None, kind: str = None) -> str:
  """Get info such as the name, kind, purchase date, and manufacturer of currently registered robots."""
  return get_robots(name, kind)


def answer_with_agent(chat: AzureChatOpenAI, system_message: str, question: str):
  tools = [search_robot_manuals_tool, get_robots_tool]

  # create the chat agent
  prompt = ChatPromptTemplate.from_messages([
    SystemMessage(content=system_message),
    HumanMessage(content=question),
    MessagesPlaceholder(variable_name="agent_scratchpad")])
  # Use prompt.format(agent_scratchpad = [AIMessage(content="whatever")]) to see the actual prompt

  # The benefits for converting functions to langchain tools then back to OpenAI tools format isn't clear,
  # except we avoided handling all the intermediate steps in chat_function_calling.py.
  # Perhaps when Azure OpenAI supports OpenAI Assistant API, it will also handle intermediate steps automatically.
  agent = create_openai_tools_agent(chat, tools, prompt=prompt)
  agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
  result = agent_executor({})
  return result


if __name__ == "__main__":
  config = LLMConfig()
  chat = AzureChatOpenAI(
    azure_deployment=config.chat['deployment'],
    openai_api_version=config.chat['api_version']
  )

  system_message = """You are an expert who helps people answer robot related questions based on only the given info in this chat.
A robot's name is typically prefixed with its kind, for example, the kind for spot_jr is spot.
If you don't know the answer, respond with "I don't know"."""
  question = "If we have any spot robots, can you tell me how to change their battery?"

  result = answer_with_agent(chat, system_message, question)
  print(result)
