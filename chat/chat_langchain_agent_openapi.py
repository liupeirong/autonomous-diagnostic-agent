import sys
import yaml
from langchain.chat_models import AzureChatOpenAI

from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.tools import  Tool, tool
from langchain_core.messages import HumanMessage, SystemMessage

from langchain.agents.agent_toolkits.openapi.spec import reduce_openapi_spec
from langchain.agents.agent_toolkits.openapi import planner
from langchain.requests import RequestsWrapper

sys.path.append('./utils')
from loadenv import LLMConfig, RobotConfig
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


def create_openapi_agents_as_tools(chat: AzureChatOpenAI):
  agent_as_tools = []
  robotConfig = RobotConfig()
  for kind in robotConfig.kinds:
    with open(kind['api_spec']) as f:
      raw_api_spec = yaml.load(f, Loader=yaml.Loader)
    api_spec = reduce_openapi_spec(raw_api_spec)
    requests_wrapper = RequestsWrapper()
    agent_executor: AgentExecutor = planner.create_openapi_agent(api_spec, requests_wrapper, chat)
    # AgentExecutor is a chain
    agent_tool = Tool.from_function(
      func=agent_executor.run,
      name=f"get_{kind['name']}_maintenance_records",
      description=f"Tool for accessing maintenance records for {kind['name']} robots.")
    agent_as_tools.append(agent_tool)

  return agent_as_tools


def answer_with_openapi(chat: AzureChatOpenAI, system_message: str, question: str):
  agent_tools = create_openapi_agents_as_tools(chat)
  tools = [search_robot_manuals_tool, get_robots_tool] + agent_tools

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
  agent_executor = AgentExecutor(agent=agent, tools=tools, handle_parsing_errors=True, max_iterations=3, verbose=True)
  result = agent_executor({"question": question})
  return result


if __name__ == "__main__":
  config = LLMConfig()
  chat = AzureChatOpenAI(
    azure_deployment=config.chat['deployment'],
    openai_api_version=config.chat['api_version']
  )

  system_message = """You are an expert who helps people answer robot related questions based on only the given info in this chat.
A robot's name is typically prefixed with its kind, for example, the kind for spot_jr is spot.
Figure out the robot's name and kind from the user's question first if you can, use them for all tools. Don't make up a name or kind.
If you don't know the answer, respond with "I don't know"."""
  question = "When was spot_jr purchased and last serviced?"

  result = answer_with_openapi(chat, system_message, question)
  print(result)
