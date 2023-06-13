from dataclasses import Field, dataclass, asdict
from typing import Dict, List, Any, Type

import hydra
from langchain.embeddings.base import Embeddings
from langchain.text_splitter import TextSplitter
from langchain.vectorstores import VectorStore, Chroma
from langchain.schema import Document
from omegaconf import DictConfig, OmegaConf

from flows.base_flows import AtomicFlow
from langchain.indexes.vectorstore import VectorstoreIndexCreator, _get_default_text_splitter


class VectorStoreAtomicFlow(AtomicFlow):
    def __init__(self, vector_store_config: DictConfig, init_documents: List[Document], **kwargs):
        text_splitter: TextSplitter = hydra.utils.instantiate(vector_store_config.text_splitter)
        embeddings: Embeddings = hydra.utils.instantiate(vector_store_config.embeddings)
        self.vector_db: VectorStore = hydra.utils.instantiate(vector_store_config.vector_store_config)

        init_texts = text_splitter.split_documents(init_documents)
        if vector_store_config.init_from_documents:
            self.vector_db = self.vector_db.__class__.from_documents(init_texts, embeddings)

        vs_conf = vector_store_config.get("retriever_config", {})
        self.vector_db = self.vector_db.as_retriever(**vs_conf)
        super().__init__(
            vector_store_config=vector_store_config,
            init_documents=init_documents,
            **kwargs
        )

    def run(self, input_data: Dict[str, Any], expected_outputs: List[str]) -> Dict[str, Any]:
        if "add_documents" in input_data:
            self.vector_db.add_documents(input_data["documents"])
            return {"success": True}

        if "query" in input_data:
            retrieved_documents = self.vector_db.get_relevant_documents(input_data["query"])
            return {expected_outputs[0]: retrieved_documents}


# @dataclass
# class default_vectorstore_config:
#     vectorstore_cls: Type[VectorStore]
#     embedding: Embeddings
#     text_splitter: TextSplitter
#     vectorstore_kwargs: dict
#
#     def __init__(
#             self,
#             vectorstore_cls: Type[VectorStore] = None,
#             embedding: Embeddings = None,
#             text_splitter: TextSplitter = None,
#             vectorstore_kwargs: dict = None
#     ):
#         if not vectorstore_cls:
#             self.vectorstore_cls = Chroma
#
#         if not embedding:
#             self.embedding = OpenAIEmbeddings()
#
#         if not text_splitter:
#             self.text_splitter = _get_default_text_splitter()
#
#         if not vectorstore_kwargs:
#             self.vectorstore_kwargs = {}


# class LGVectorStoreAtomicFlow(AtomicFlow):
#     vector_store_config: Dict
#     loaders: List = None
#     documents: List = None
#     with_sources: bool = False
#
#     def __init__(self, **kwargs):
#         if "vector_store_config" not in kwargs:
#             kwargs["vector_store_config"] = asdict(default_vectorstore_config())
#
#         super().__init__(**kwargs)
#
#         self.flow_state["vsi_creator"] = VectorstoreIndexCreator(**self.vector_store_config)
#
#         if hasattr(self, "loaders"):
#             if self.loaders:
#                 self.vsi = self.flow_state["vsi_creator"].from_loaders(self.loaders)
#
#         assert hasattr(self, "documents")
#         if self.documents:
#             self.vsi = self.flow_state["vsi_creator"].from_documents(self.documents)
#
#     def run(self, input_data: Dict[str, Any], expected_outputs: List[str]) -> Dict[str, Any]:
#         if "loaders" in input_data:
#             self.loaders = input_data["loaders"]
#             self.vsi = self.flow_state["vsi_creator"].from_loaders(input_data["loaders"])
#
#         if "documents" in input_data:
#             self.documents = input_data["documents"]
#             self.vsi = self.flow_state["vsi_creator"].from_documents(input_data["documents"])
#
#         question = input_data["query"]
#
#         if self.with_sources:
#             answer = self.vsi.query_with_sources(question=question)
#         else:
#             answer = self.vsi.query(question=question)
#         return {expected_outputs[0]: answer}


if __name__ == "__main__":
    cfg = OmegaConf.create({
        "text_splitter": {
            "_target_": "langchain.text_splitter.RecursiveCharacterTextSplitter",
            "chunk_size": 1000,
            "chunk_overlap": 0
        },
        "embeddings": {
            "_target_": "langchain.embeddings.OpenAIEmbeddings",
        },
        "vector_store_config": {
            "_target_": "langchain.vectorstores.Chroma"
        },
        "init_from_documents": True,
        "retriever_config": {

        },
        "name": "lg_vectorstore_chroma_openai",
        "description": "embeds texts with openai embeddings using chroma vectorstore db",
    })

    from langchain.document_loaders import TextLoader

    loader = TextLoader('data/state_of_the_union.txt', encoding='utf8')
    documents = loader.load()

    vs = VectorStoreAtomicFlow(
        name="lg_vectorstore_chroma_openai",
        description="embeds texts with openai embeddings using chroma vectorstore db",
        vector_store_config=cfg,
        init_documents=documents
    )

    tm = vs.package_task_message(
        recipient_flow=vs,
        task_name="",
        task_data={"query": "What did the president say about Ketanji Brown Jackson"},
        expected_outputs=["answer"]
    )

    print(vs(tm))
    # from langchain.text_splitter import RecursiveCharacterTextSplitter
    # from langchain.embeddings import OpenAIEmbeddings
    # from langchain.vectorstores import Chroma
    #
    #
    # text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
    # texts = text_splitter.split_documents(documents)
    #
    # embeddings = OpenAIEmbeddings()
    #
    # db = Chroma.from_documents(texts, embeddings)
    #
    # retriever = db.as_retriever()
    # db.persist()