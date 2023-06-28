from typing import Dict, List, Any

from langchain.vectorstores import VectorStore, Chroma, Pinecone
from langchain.vectorstores.base import VectorStoreRetriever

from flows.base_flows import AtomicFlow

from flows.utils.caching_utils import flow_run_cache


class GenericLCVectorStore(AtomicFlow):
    vector_db: VectorStoreRetriever

    def __init__(
            self,
            vectorstore: VectorStore,
            retriever_config: Dict = None,
            **kwargs
    ):

        if retriever_config is None:
            retriever_config = {}

        super().__init__(
            retriever_config=retriever_config,
            clear_flow_namespace_on_run_end=False,
            **kwargs
        )
        self.KEYS_TO_IGNORE_HASH += ["vector_db"]  # but needs to override __repr__ to have meaningful hash
        # Not passed in the abstract because for some vectorstore, deepcopy fails.
        self.vector_db = vectorstore.as_retriever(**retriever_config)

    # def __repr__(self):
    #     # override for caching, needs to repr that without repr all sub-object with their pointers
    #     # type_of_vectorstore = self.vector_db.vectorstore.__class__.__name__
    #     return

    @flow_run_cache()
    def run(self, input_data: Dict[str, Any], output_keys: List[str]) -> Dict[str, Any]:
        # vector_db = self.flow_config["vector_db"]
        if "add_documents" in input_data:
            self.vector_db.add_documents(input_data["documents"])
            return {"success": True}

        if "query" in input_data:
            retrieved_documents = self.vector_db.get_relevant_documents(input_data["query"])
            return {output_keys[0]: retrieved_documents}



if __name__ == "__main__":
    from langchain.document_loaders import TextLoader

    loader = TextLoader('data/state_of_the_union.txt', encoding='utf8')
    documents = loader.load()

    from langchain.text_splitter import RecursiveCharacterTextSplitter
    from langchain.embeddings import OpenAIEmbeddings
    from langchain.vectorstores import Chroma

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
    texts = text_splitter.split_documents(documents)

    embeddings = OpenAIEmbeddings()

    db = Chroma.from_documents(texts, embeddings)

    glcv = GenericLCVectorStore(
        name="Chroma vector-store",
        description="vector database",
        vectorstore=db,
        expected_inputs=["query"],
        output_keys=["answer"]
    )

    tm = glcv.package_task_message(
        recipient_flow=glcv,
        task_name="",
        task_data={"query": "What did the president say about Ketanji Brown Jackson"},
        output_keys=["answer"]
    )

    import time
    t0 = time.time()
    _ = glcv(tm)
    t1 = time.time()
    _ = glcv(tm)
    t2 = time.time()

    print(f"First: {t1 -t0}, second {t2 - t1}")


    #
    # retriever = db.as_retriever()
    # db.persist()