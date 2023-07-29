from copy import deepcopy
from typing import Dict, List, Any, Optional

import uuid
import faiss

from langchain.docstore import InMemoryDocstore
from langchain.embeddings import OpenAIEmbeddings
from langchain.schema import Document
from langchain.vectorstores import VectorStore, Chroma, FAISS, Pinecone
from langchain.vectorstores.base import VectorStoreRetriever

from chromadb import Client as ChromaClient

from flows.base_flows import AtomicFlow

class ChromaDBFlow(AtomicFlow):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.client = ChromaClient()
        self.collection = self.client.get_or_create_collection(name=self.flow_config["name"])

    def get_input_keys(self) -> List[str]:
        return self.flow_config["input_keys"]
    
    def get_output_keys(self) -> List[str]:
        return self.flow_config["output_keys"]
    
    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        api_key = self._get_from_state("api_keys")["openai"]
        embeddings = OpenAIEmbeddings(openai_api_key=api_key)
        response = {}
        
        operation = input_data["operation"]
        if operation not in ["write", "read"]:
            raise ValueError(f"Operation '{operation}' not supported")
        
        content = input_data["content"]
        if operation == "read":
            if not isinstance(content, str):
                raise ValueError(f"content(query) must be a string during read, got {type(content)}: {content}")
            query = content
            query_result = self.collection.query(
                query_embeddings=embeddings.embed_query(query),
                n_results=self.flow_config["n_results"]
            )
            
            response["retrieved"] = [doc for doc in query_result["documents"]]

        elif operation == "write":
            if not isinstance(content, list):
                content = [content]
            documents = content
            self.collection.add(
                ids=[str(uuid.uuid4()) for _ in range(len(documents))],
                embeddings=embeddings.embed_documents(documents),
                documents=documents
            )
            response["retrieved"] = ""

        return response
    
    