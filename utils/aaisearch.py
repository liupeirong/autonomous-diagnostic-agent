from typing import List
from loadenv import LLMConfig
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
  SearchIndex,
  SearchFieldDataType,
  CorsOptions,
  SimpleField,
  SearchableField,
  SearchField,
  VectorSearch,
  VectorSearchAlgorithmKind,
  HnswAlgorithmConfiguration,
  HnswParameters,
  VectorSearchAlgorithmMetric,
  ExhaustiveKnnAlgorithmConfiguration,
  ExhaustiveKnnParameters,
  SemanticConfiguration,
  SemanticPrioritizedFields,
  SemanticField,
  SemanticSearch,
  VectorSearchProfile,
)

class AAISearch:
  search_index_client: SearchIndexClient = None

  def __init__(self):
    config = LLMConfig().search
    credential = AzureKeyCredential(config['api_key'])
    self.search_index_client = SearchIndexClient(endpoint=config['endpoint'], credential=credential)


  def delete_index(self, name: str):
    print(f"deleting index {name}")
    self.search_index_client.delete_index(name)


  def get_index(self, name: str) -> SearchIndex:
    return self.search_index_client.get_index(name)


  def create_index(self, name: str) -> SearchIndex:
    try:
      self.search_index_client.get_index(name)
      self.search_index_client.delete_index(name)
    except:
      pass

    fields = [
        SimpleField(name="id", type=SearchFieldDataType.String, key=True),
        SimpleField(name="language", type=SearchFieldDataType.String, filterable=True),
        SimpleField(name="kind", type=SearchFieldDataType.String, filterable=True),
        SearchableField(name="title", type=SearchFieldDataType.String),
        SearchableField(name="description", type=SearchFieldDataType.String),
        SearchableField(name="content", type=SearchFieldDataType.String),
        SearchableField(name="h1", type=SearchFieldDataType.String),
        SearchableField(name="h2", type=SearchFieldDataType.String),
        SearchableField(name="h3", type=SearchFieldDataType.String),
        SearchField(
            name="contentVector",
            type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
            searchable=True,
            # Size of the vector created by the text-embedding-ada-002 model.
            vector_search_dimensions=1536,
            vector_search_profile_name="myHnswProfile",
        ),
    ]

    # The "content" field should be prioritized for semantic ranking.
    semantic_config = SemanticConfiguration(
        name="default",
        prioritized_fields=SemanticPrioritizedFields(
            title_field=SemanticField(field_name="title"),
            keywords_fields=[
              SemanticField(field_name="kind"),
              SemanticField(field_name="h1"),
              SemanticField(field_name="h2"),
              SemanticField(field_name="h3")],
            content_fields=[SemanticField(field_name="content")],
        ),
    )

    # For vector search, we want to use the HNSW (Hierarchical Navigable Small World)
    # algorithm (a type of approximate nearest neighbor search algorithm) with cosine
    # distance.
    vector_search = VectorSearch(
        algorithms=[
            HnswAlgorithmConfiguration(
                name="myHnsw",
                kind=VectorSearchAlgorithmKind.HNSW,
                parameters=HnswParameters(
                    m=4,
                    ef_construction=400,
                    ef_search=500,
                    metric=VectorSearchAlgorithmMetric.COSINE,
                ),
            ),
            ExhaustiveKnnAlgorithmConfiguration(
                name="myExhaustiveKnn",
                kind=VectorSearchAlgorithmKind.EXHAUSTIVE_KNN,
                parameters=ExhaustiveKnnParameters(
                    metric=VectorSearchAlgorithmMetric.COSINE
                ),
            ),
        ],
        profiles=[
            VectorSearchProfile(
                name="myHnswProfile",
                algorithm_configuration_name="myHnsw",
            ),
            VectorSearchProfile(
                name="myExhaustiveKnnProfile",
                algorithm_configuration_name="myExhaustiveKnn",
            ),
        ],
    )

    # Create the semantic settings with the configuration
    semantic_search = SemanticSearch(configurations=[semantic_config])
    cors_options = CorsOptions(allowed_origins=["*"], max_age_in_seconds=60)
    index = SearchIndex(name=name, fields=fields, cors_options=cors_options, semantic_search=semantic_search, vector_search=vector_search)
    result = self.search_index_client.create_or_update_index(index=index)
    return result


  def upload_documents(self, name: str, documents: List[dict]):
    search_client: SearchClient = self.search_index_client.get_search_client(name)
    search_client.upload_documents(documents)

  
  def get_search_client(self, name: str) -> SearchClient:
    return self.search_index_client.get_search_client(name)
