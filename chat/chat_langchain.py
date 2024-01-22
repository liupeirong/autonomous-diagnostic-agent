import sys
from langchain.chat_models import AzureChatOpenAI
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableParallel, RunnablePassthrough
from langchain.embeddings import AzureOpenAIEmbeddings
from langchain.vectorstores.azuresearch import AzureSearch, AzureSearchVectorStoreRetriever
from langchain.prompts import ChatPromptTemplate

sys.path.append('./utils')
from loadenv import LLMConfig

#
# Note
# To run this file, you must install azure-search-documents==11.4.0b8
#
def create_search_retriever(config: LLMConfig) -> AzureSearchVectorStoreRetriever:
  # here using OpenAIEmbeddings will fail
  embeddings = AzureOpenAIEmbeddings(
    azure_endpoint=config.aoai['endpoint'],
    openai_api_key=config.aoai['api_key'],
    openai_api_version=config.embedding['api_version'],
    azure_deployment=config.embedding['deployment'],
    chunk_size=1)
  # here AzureSearch is only compatible with azure-search-documents==11.4.0b8
  vector_store = AzureSearch(
    azure_search_endpoint=config.search['endpoint'],
    azure_search_key=config.search['api_key'],
    index_name=config.search['index_name'],
    search_type='hybrid',
    embedding_function=embeddings.embed_query)
  retriever = vector_store.as_retriever(search_kwargs={"k": 3})
  return retriever


def answer_with_chain(config: LLMConfig, chat: AzureChatOpenAI, template: str, question: str) -> str:
  prompt = ChatPromptTemplate.from_template(template)
  outputParser = StrOutputParser()
  retriever = create_search_retriever(config)

  # this means we take input and 
  #  run retriever on it and pass to the next function in parameter "context"
  #  run passthrough on it and pass to the next function in parameter "question"
  setup_and_retrieval = RunnableParallel(
      {"context": retriever, "question": RunnablePassthrough()}
  )

  chain = setup_and_retrieval | {"response": prompt | chat | outputParser, "sources": RunnablePassthrough()}
  result = chain.invoke(question)
  # get unique document sources
  sources = []
  sources += (x.metadata['title'] for x in result['sources']['context'])
  return result['response'], list(dict.fromkeys(sources))


if __name__ == "__main__":
  config = LLMConfig()
  chat = AzureChatOpenAI(
    azure_deployment=config.chat['deployment'],
    openai_api_version=config.chat['api_version']
  )

  template = """You are an expert who helps people answer robot related questions based on only the given context.
A robot's name is typically prefixed with its kind, for example, the kind for spot_jr is spot.
If you don't know the answer, respond with "I don't know".
{context}

Question: {question}
"""

  question = "What api can I use to program spot_jr?"
  result, sources = answer_with_chain(config, chat, template, question)
  print(f"answer: {result}\nfrom: {';'.join(sources)}")
