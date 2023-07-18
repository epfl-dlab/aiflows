from copy import deepcopy
from typing import Dict, List, Any, Optional

import faiss

from langchain.docstore import InMemoryDocstore
from langchain.embeddings import OpenAIEmbeddings
from langchain.schema import Document
from langchain.vectorstores import VectorStore, Chroma, FAISS, Pinecone
from langchain.vectorstores.base import VectorStoreRetriever

from flows.base_flows import AtomicFlow

class VectorStoreFlow(AtomicFlow):
    REQUIRED_KEYS_CONFIG = ["type", "api_keys"]
    REQUIRED_KEYS_CONSTRUCTOR = ["vector_db"]

    vector_db: VectorStoreRetriever

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @classmethod
    def _set_up_retriever(cls, config: Dict[str, Any]) -> Dict[str, Any]:
        embeddings = OpenAIEmbeddings(openai_api_key=config["api_keys"]["openai"])
        kwargs = {}

        vs_type = config["type"]

        if vs_type == "chroma":
            vectorstore = Chroma(config["name"], embedding_function=embeddings)
        elif vs_type == "faiss":
            index = faiss.IndexFlatL2(config.get("embedding_size", 1536)) 
            vectorstore = FAISS(
                embedding_function=embeddings.embed_query,
                index=index,
                docstore=InMemoryDocstore({}),
                index_to_docstore_id={}
            )
        else:
            raise NotImplementedError(f"Vector store '{vs_type}' not implemented")
        
        kwargs["vector_db"] = vectorstore.as_retriever(**config.get("retriever_config", {}))
        
        return kwargs

    @classmethod
    def instantiate_from_config(cls, config: Dict[str, Any]):
        flow_config = deepcopy(config)

        kwargs = {"flow_config": flow_config}
        kwargs["input_data_transformations"] = cls._set_up_data_transformations(config["input_data_transformations"])
        kwargs["output_data_transformations"] = cls._set_up_data_transformations(config["output_data_transformations"])

        kwargs.update(cls._set_up_retriever(flow_config))

        return cls(**kwargs)

    @staticmethod
    def package_documents(documents: List[str]) -> List[Document]:
        # TODO(yeeef): support metadata
        return [Document(page_content=doc, metadata={"": ""}) for doc in documents]

    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        response = {}
        
        operation = input_data["operation"]
        assert operation in ["write", "read"], f"Operation '{operation}' not supported"
        
        content = input_data["content"]
        if operation == "read":
            assert isinstance(content, str), f"Content must be a string, got {type(content)}"
            query = content
            retrieved_documents = self.vector_db.get_relevant_documents(query)
            response["retrieved"] = [doc.page_content for doc in retrieved_documents]
        elif operation == "write":
            if isinstance(content, str):
                content = [content]
            assert isinstance(content, list), f"Content must be a list of strings, got {type(content)}"
            documents = content
            documents = self.package_documents(documents)
            self.vector_db.add_documents(documents)
            response["retrieved"] = ""

        return response
