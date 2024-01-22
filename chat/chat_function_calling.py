import sys
from openai import AzureOpenAI
from openai.types.chat import ChatCompletionMessage
import json
import logging
import pprint

sys.path.append('./utils')
from loadenv import LLMConfig
sys.path.append('./chat/functions')
from robot_general import get_robots, search_robot_manuals

# Both OpenAI and Azure OpenAI use the same concept for Function Calling.
# It is also the basis for "Tools" in the new OpenAI Assistant API.
# However, tools in OpenAI, such as "retrieval" and "code_interpreter" are not yet in Azure OpenAI. 2023-12
def answer_with_tools(aoai: AzureOpenAI, aoai_deployment: str, user_question: str, system_message: dict, tools: list):
  messages = [system_message, {"role": "user", "content": user_question}]

  num_turns = 0
  while True:
    print_llm_messages(messages)
    response = aoai.chat.completions.create(
        model=aoai_deployment,
        messages=messages,
        tools=tools,
        tool_choice="auto", # let the model decide. "none" means don't call, or specify which tool to always call. 
    )
    result_message = response.choices[0].message
    tool_calls = result_message.tool_calls

    # no more tools to call
    if not tool_calls:
      return result_message

    # doesn't make sense to call tools over and over
    if num_turns > 2:
      logging.warning("force terminated.")
      return result_message

    # call tools, add tool results to messages
    result_message.content = "" if not result_message.content else result_message.content
    messages.append(result_message)
    for tool_call in tool_calls:
      if tool_call.function.name == "get_robots":
        args = json.loads(tool_call.function.arguments)
        function_result = get_robots(**args)
        messages.append({
          "tool_call_id": tool_call.id,
          "role": "tool",
          "name": tool_call.function.name,
          "content": function_result
        })
        num_turns += 1
      elif tool_call.function.name == "search_robot_manuals":
        args = json.loads(tool_call.function.arguments)
        function_result = search_robot_manuals(**args)
        messages.append({
          "tool_call_id": tool_call.id,
          "role": "tool",
          "name": tool_call.function.name,
          "content": function_result
        })
        num_turns += 1


def answer_with_datasource(aoai, aoai_deployment, user_question, system_message, tools, dataSources):
  messages = [system_message, {"role": "user", "content": user_question}]

  num_turns = 0
  while True:
    response = aoai.chat.completions.create(
        model=aoai_deployment,
        messages=messages,
        tools=tools,
        tool_choice="auto",
        extra_body={
          "dataSources": dataSources
        }
    )
    result_message = response.choices[0].message
    tool_calls = result_message.tool_calls

    # no more tools to call
    if not tool_calls:
      return result_message

    # doesn't make sense to call tools over and over
    if num_turns > 1:
      logging.warning("force terminated.")
      return(result_message)

    # call tools, add tool results to messages
    result_message.content = "" if not result_message.content else result_message.content
    messages.append(result_message)
    for tool_call in tool_calls:
      if tool_call.function.name == "get_robots":
        args = json.loads(tool_call.function.arguments)
        function_result = get_robots(**args)
        messages.append({
          "tool_call_id": tool_call.id,
          "role": "tool",
          "name": tool_call.function.name,
          "content": function_result
        })
        num_turns += 1


def print_llm_messages(msg):
  if logging.getLogger().level > logging.INFO:
    return

  print("-----------------------------------LLM message(s)---------------------------------------------------")
  pp = pprint.PrettyPrinter(width=160)
  if isinstance(msg, list):
    for m in msg:
      if isinstance(m, dict):
        pp.pprint(m)
      elif isinstance(m, ChatCompletionMessage):
        pp.pprint(dict(m))
  if isinstance(msg, ChatCompletionMessage):
    pp.pprint(dict(msg))


tools = [
  {
    "type": "function",
    "function": {
      "name": "get_robots",
      "description": "Get the name, kind, purchase date, and manufacturer of currently registered robots",
      "parameters": {
          "type": "object",
          "properties": {
              "name": {"type": "string", "description": "The name of the robot to get information about"},
              "kind": {"type": "string", "description": "the kind of the robot to get information about"},
          },
          "required": [],
      },
    },
  },
  {
    "type": "function",
    "function": {
      "name": "search_robot_manuals",
      "description": "Search the robot manuals for robot faults, troubleshooting guides, development API etc.",
      "parameters": {
          "type": "object",
          "properties": {
              "query": {"type": "string", "description": "The user's query for semantic and vector search"},
              "kind": {"type": "string", "description": "the kind of the robot to get information about"},
          },
          "required": ["query"],
      },
    },
  }
]


if __name__ == "__main__":
  logging.basicConfig(level=logging.INFO)

  config = LLMConfig()
  api_version, deployment = config.chat["api_version"], config.chat['deployment']
  aoai = AzureOpenAI(api_version=api_version)

  system_message = {"role": "system", "content": 
    """You are an expert who helps people troubleshoot robot related issues.
    A robot's name is typically prefixed with its kind, for example, the kind for spot_jr is spot.
    Try identify the kind of the robot first so you can narrow down when searching for info in tools. 
    Respond only with the info from the provided context or tools.
    If you don't know the answer, respond with "I don't know"."""}
  # question = "My robot spot_jr seems to have a leg motor broken. Can you help me gather all the info related to this robot that might help me fix it?"
  question = "My robot spot_jr can't make left turns. Was it purchased more than 1 year ago? Is there an API I can call?"

  res = answer_with_tools(aoai, deployment, question, system_message, tools)
  print_llm_messages(res)

  #---------------------------------------------------------------------------------------------------
  # instead of using function calling, try dataSources ("use your data" in OpenAI)
  # note that even for gpt4, once you use dataSources, it doesn't think to call tools any more.
  dataSources = [
    {
      "type": "AzureCognitiveSearch",
      "parameters": {
        "endpoint": config.search['endpoint'],
        "key": config.search['api_key'],
        "indexName": config.search['index_name'],
      }
    },
  ]
  aoai_ds = AzureOpenAI(
    base_url=f"{config.aoai['endpoint']}/openai/deployments/{deployment}/extensions",
    api_version=api_version,
  )
  res = answer_with_datasource(aoai_ds, deployment, question, system_message, [tools[0]], dataSources)
  print_llm_messages(res)
