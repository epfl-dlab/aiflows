from dataclasses import Field, dataclass, asdict
from typing import Dict, List, Any, Type

from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.embeddings.base import Embeddings
from langchain.text_splitter import TextSplitter
from langchain.vectorstores import VectorStore, Chroma

from flows.base_flows import AtomicFlow
from langchain.indexes.vectorstore import VectorstoreIndexCreator, _get_default_text_splitter

from flows.utils.caching_utils import flow_run_cache


@dataclass
class default_vectorstore_config:
    vectorstore_cls: Type[VectorStore]
    embedding: Embeddings
    text_splitter: TextSplitter
    vectorstore_kwargs: dict

    def __init__(
            self,
            vectorstore_cls: Type[VectorStore] = None,
            embedding: Embeddings = None,
            text_splitter: TextSplitter = None,
            vectorstore_kwargs: dict = None
    ):
        if not vectorstore_cls:
            self.vectorstore_cls = Chroma

        if not embedding:
            self.embedding = OpenAIEmbeddings()

        if not text_splitter:
            self.text_splitter = _get_default_text_splitter()

        if not vectorstore_kwargs:
            self.vectorstore_kwargs = {}


class LGVectorStoreAtomicFlow(AtomicFlow):
    vector_store_config: Dict
    loaders: List = None
    documents: List = None
    with_sources: bool = False

    def __init__(self, **kwargs):
        if "vector_store_config" not in kwargs:
            kwargs["vector_store_config"] = asdict(default_vectorstore_config())

        super().__init__(**kwargs)

        self.flow_state["vsi_creator"] = VectorstoreIndexCreator(**self.vector_store_config)

        if hasattr(self, "loaders"):
            if self.loaders:
                self.vsi = self.flow_state["vsi_creator"].from_loaders(self.loaders)

        assert hasattr(self, "documents")
        if self.documents:
            self.vsi = self.flow_state["vsi_creator"].from_documents(self.documents)

    def run(self, input_data: Dict[str, Any], expected_outputs: List[str]) -> Dict[str, Any]:
        if "loaders" in input_data:
            self.loaders = input_data["loaders"]
            self.vsi = self.flow_state["vsi_creator"].from_loaders(input_data["loaders"])

        if "documents" in input_data:
            self.documents = input_data["documents"]
            self.vsi = self.flow_state["vsi_creator"].from_documents(input_data["documents"])

        question = input_data["query"]
        # time.sleep(0.5)
        # answer = "DEFAULT"
        if self.with_sources:
            answer = self.vsi.query_with_sources(question=question)
        else:
            answer = self.vsi.query(question=question)
        return {expected_outputs[0]: answer}


if __name__ == "__main__":
    from langchain.document_loaders import TextLoader

    loader = TextLoader('data/state_of_the_union.txt')

    lgvs = LGVectorStoreAtomicFlow(
        name="VectorStoreLG",
        description="Index using vector store over 'state_of_the_union.txt'",
        expected_inputs=["query"],
        loaders=[loader]
    )

    task_message = lgvs.package_task_message(
        recipient_flow=lgvs,
        task_name="",
        task_data={"query": "What did the president say about Ketanji Brown Jackson",
                   "loaders": [loader]},
        expected_outputs=["answer"]
    )

    import time

    t0 = time.time()
    print(lgvs(task_message))
    t1 = time.time()
    print(lgvs(task_message))
    t2 = time.time()

    print(t1 - t0)
    print(t2 - t1)