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

    def get_input_keys(self, data: Optional[Dict[str, Any]] = None):
        pre_runtime_input_keys = self.flow_config["input_keys"]
        if data is None:
            return pre_runtime_input_keys

        ret = []
        for key in data.keys():
            if key in pre_runtime_input_keys:
                ret.append(key)
        return ret

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
        
        documents = input_data.get("write", None)
        query = input_data.get("query", None)

        if documents: # write documents to vector store
            documents = self.package_documents(documents)
            self.vector_db.add_documents(documents)
            response["retrieved"] = ""

        if query: # retrieve documents from vector store
            retrieved_documents = self.vector_db.get_relevant_documents(query)
            response["retrieved"] = [doc.page_content for doc in retrieved_documents]

        return response


"""
if __name__ == "__main__":
    # from langchain.document_loaders import TextLoader

    # loader = TextLoader('data/state_of_the_union.txt', encoding='utf8')
    # documents = loader.load()

    # from langchain.text_splitter import RecursiveCharacterTextSplitter
    # from langchain.vectorstores import Chroma

    # text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
    # texts = text_splitter.split_documents(documents)

    # embeddings = OpenAIEmbeddings()

    # db = Chroma.from_documents(texts, embeddings)


    flow_config = {
        "name": "Chroma vector-store",
        "description": "vector database",
        "vectorstore_type": "chroma",
        "verbose": False,
        "namespace_clearing_after_run": False,
        "expected_inputs": ["documents", "query"],
        "expected_outputs": ["answer"],
        "retriever_config": {}
    }

    glcv = GenericLCVectorStore.instantiate_from_config(flow_config)

    tm1 = glcv.package_task_message(
        recipient_flow=glcv,
        task_name="",
        task_data={
            "documents": [Document(page_content="Lorem ipsum dolor sit amet, consectetur adipiscing elit. Quisque dignissim mi sem.")],
            "query": None
        },
        expected_outputs=["answer"]
    )

    tm2 = glcv.package_task_message(
        recipient_flow=glcv,
        task_name="",
        task_data={
            "documents": None,
            "query": "bla"
        },
        expected_outputs=["answer"]
    )

    tm3 = glcv.package_task_message(
        recipient_flow=glcv,
        task_name="",
        task_data={
            "documents": [Document(page_content="Suspendisse sit amet neque faucibus, scelerisque arcu vel, congue lectus.")],
            "query": "lectus"
        },
        expected_outputs=["answer"]
    )

    for tm in [tm1, tm2, tm3]:
        response = glcv(tm)
        print(response.data, '\n')

    # import time
    # t0 = time.time()
    # _ = glcv(tm)
    # t1 = time.time()
    # _ = glcv(tm)
    # t2 = time.time()

    # print(f"First: {t1 -t0}, second {t2 - t1}")


    #
    # retriever = db.as_retriever()
    # db.persist()
"""
    