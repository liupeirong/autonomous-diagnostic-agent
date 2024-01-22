import sys
import string
from langchain.embeddings import AzureOpenAIEmbeddings
from langchain.document_loaders.recursive_url_loader import RecursiveUrlLoader
from langchain.text_splitter import HTMLHeaderTextSplitter

sys.path.append('./utils')
from loadenv import LLMConfig, RobotConfig
from adls import ADLSDocStore
from chroma import ChromaDBClient
from aaisearch import AAISearch


def crawl_and_store_raw_manuals(docStore, root_dir, robotConfig):
  max_depth = robotConfig.url_max_depth
  for kind in robotConfig.kinds:
    toPath, toExt = f"{kind['name']}/{root_dir}/raw", "html"
    docStore.clear_path(toPath)
    for manual in kind["manuals"]:
      print(f"{kind['name']}: loading {manual}")
      # keep raw html format
      loader = RecursiveUrlLoader(url=manual, max_depth=max_depth)
      docs = loader.load()
      for doc in docs:
        for key in doc.metadata:
          doc.metadata[key] = make_printable(str(doc.metadata[key]))
        doc.page_content = make_printable(doc.page_content)
      docStore.store_docs(path=toPath, ext=toExt, docs=docs)
      print(f"{kind['name']}: saved {len(docs)} raw docs")


def chunk_manuals(docStore, root_dir, robotConfig):
  html_splitter = HTMLHeaderTextSplitter(robotConfig.headers_to_split_on)
  for kind in robotConfig.kinds:
    fromPath, fromExt = f"{kind['name']}/{root_dir}/raw", "html"
    toPath, toExt = f"{kind['name']}/{root_dir}/split", "txt"
    docStore.clear_path(toPath)
    docs = docStore.get_docs(path=fromPath, ext=fromExt)
    for doc in docs:
      content, metadata = docStore.get_file(doc)
      splits = html_splitter.split_text(content)
      for split in splits:
        for key in split.metadata:
          split.metadata[key] = make_printable(str(split.metadata[key]))
        split.metadata.update(metadata)
      docStore.store_docs(path=toPath, ext=toExt, docs=splits)
      print(f"{kind['name']}: {metadata['source']}: saved {len(splits)} splits")


def embed_manuals(docStore, root_dir, robotConfig, llmConfig, vectorDB):
  embeddings = AzureOpenAIEmbeddings(
    azure_deployment=llmConfig.embedding['deployment'],
    openai_api_version=llmConfig.embedding['api_version']
  )
  dbClient = vectorDB.create_db(llmConfig.vector_db['db_name'])

  for kind in robotConfig.kinds:
    fromPath, fromExt = f"{kind['name']}/{root_dir}/split", "txt"
    docs = docStore.get_docs(path=fromPath, ext=fromExt)
    for doc in docs:
      content, metadata = docStore.get_file(doc.name)
      id = doc.name.split('/')[-1]
      metadata.update({"kind": kind['name']})
      metadata.update({"uri": doc.name})
      emb = embeddings.embed_documents([content])
      dbClient.add(embeddings=emb, metadatas=[metadata], ids=[id])
      print(f"{kind['name']}: saved embedding for {id}")


def index_manuals(docStore, llmConfig, vectorDB, searchClient):
  searchIndexName = llmConfig.search['index_name']
  searchClient.create_index(searchIndexName)
  dbClient = vectorDB.get_db(llmConfig.vector_db['db_name'])
  docs = dbClient.get(include=[])
  nDocs = len(docs['ids'])
  for i in range(nDocs):
    id = docs['ids'][i]
    doc = dbClient.get(ids=[id], include=['embeddings', 'metadatas'])
    metadata, embedding = doc['metadatas'][0], doc['embeddings'][0]
    content, _ = docStore.get_file(metadata['uri'])
    item = {
      "id": id.replace('.', '_'),
      "language": metadata['language'],
      "kind": metadata['kind'],
      "title": metadata['title'],
      "description": metadata['description'] if "description" in metadata else '',
      "h1": metadata['h1'] if "h1" in metadata else '',
      "h2": metadata['h2'] if "h2" in metadata else '',
      "h3": metadata['h3'] if "h3" in metadata else '',
      "content": content,
      "contentVector": embedding,
    }
    searchClient.upload_documents(name=searchIndexName, documents=[item])  
    print(f"{metadata['kind']}: saved search index for {id}")


def make_printable(somestr):
  printable = set(string.printable) # convert all metadata to printable characters
  return ''.join(filter(lambda x: x in printable, str(somestr)))


if __name__ == "__main__":
  root_dir = 'manuals'
  docStore = ADLSDocStore()
  robotConfig = RobotConfig() 

  crawl_and_store_raw_manuals(docStore, root_dir, robotConfig)
  chunk_manuals(docStore, root_dir, robotConfig)

  llmConfig = LLMConfig()
  vectorDB = ChromaDBClient()
  embed_manuals(docStore, root_dir, robotConfig, llmConfig, vectorDB)

  searchClient = AAISearch()
  index_manuals(docStore, llmConfig, vectorDB, searchClient)