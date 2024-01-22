import sys
from promptflow import PFClient
from promptflow.entities import AzureOpenAIConnection

# run this from project root

sys.path.append('utils')
from loadenv import LLMConfig


def create_aoai_connection(pf: PFClient):
  llmConfig = LLMConfig()
  connection_name = llmConfig.promptflow["aoai_connection_name"]
  connection = AzureOpenAIConnection(
      name=connection_name,
      api_key=llmConfig.aoai["api_key"],
      api_base=llmConfig.aoai["endpoint"],
      api_type="azure",
      api_version=llmConfig.chat["api_version"],
  )

  print(f"Creating connection {connection.name}...")
  result = pf.connections.create_or_update(connection)
  print(result)


if __name__ == "__main__":
  pf = PFClient()
  create_aoai_connection(pf)

  inputs = {"question": "What robots do we have?"}
  result = pf.test(flow="chat_flow", inputs=inputs)
  print(result)