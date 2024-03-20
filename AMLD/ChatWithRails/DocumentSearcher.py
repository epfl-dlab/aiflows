

import os
from typing import Dict, List, Any

import uuid
from copy import deepcopy
from langchain.embeddings import OpenAIEmbeddings

from aiflows.messages import FlowMessage
from aiflows.base_flows import AtomicFlow
from langchain.text_splitter import CharacterTextSplitter
from langchain.document_loaders import TextLoader
from langchain.vectorstores import Chroma
import hydra

class DocumentSearcher(AtomicFlow):
    def __init__(self, backend,**kwargs):
        super().__init__(**kwargs)
        
        self.backend = backend

    def set_up_flow_state(self):
        super().set_up_flow_state()
        self.flow_state["db_created"] =False
    
    @classmethod
    def _set_up_backend(cls, config):
        """ This instantiates the backend of the flow from a configuration file.
        
        :param config: The configuration of the backend.
        :type config: Dict[str, Any]
        :return: The backend of the flow.
        :rtype: Dict[str, LiteLLMBackend]
        """
        kwargs = {}

        kwargs["backend"] = \
            hydra.utils.instantiate(config['backend'], _convert_="partial")
        
        return kwargs
    
    @classmethod
    def instantiate_from_config(cls, config):
        """ This method instantiates the flow from a configuration file
        
        :param config: The configuration of the flow.
        :type config: Dict[str, Any]
        :return: The instantiated flow.
        :rtype: ChromaDBFlow
        """
        flow_config = deepcopy(config)

        kwargs = {"flow_config": flow_config}

        # ~~~ Set up backend ~~~
        kwargs.update(cls._set_up_backend(flow_config))

        # ~~~ Instantiate flow ~~~
        return cls(**kwargs)
    
    
    def get_embeddings_model(self):
        api_information = self.backend.get_key()
        if api_information.backend_used == "openai":
            embeddings = OpenAIEmbeddings(openai_api_key=api_information.api_key)
        else:
            # ToDo: Add support for Azure
            embeddings = OpenAIEmbeddings(openai_api_key=os.getenv("OPENAI_API_KEY"))
        return embeddings
    
    
    def get_db(self):
        print("loading db ...")
        db_created = self.flow_state["db_created"]
        
        if hasattr(self, 'db'):
            #do nothing
            db = self.db
        
        elif db_created:
             # load from disk
            db = Chroma(
                persist_directory=self.flow_config["persist_directory"],
                embedding_function=self.get_embeddings_model()
            )
        else:
            # create db and save to disk
            full_docs = []
            text_splitter = CharacterTextSplitter(
                chunk_size=self.flow_config["chunk_size"],
                chunk_overlap=self.flow_config["chunk_overlap"]
            )
            
            for path in self.flow_config["paths_to_data"]:
                loader =  TextLoader(path)
                documents = loader.load()
                docs = text_splitter.split_documents(documents)
                full_docs.extend(docs)
                
            db = Chroma.from_documents(
                full_docs,
                self.get_embeddings_model(),
                persist_directory=self.flow_config["persist_directory"]
            )
            
        self.flow_state["db_created"] = True
        print("finished_loading")
        return db
        
            
    
    def run(self, input_message: FlowMessage):
        """ This method runs the flow. It runs the ChromaDBFlow. It either writes or reads memories from the database.
        
        :param input_message: The input message of the flow.
        :type input_message: FlowMessage
        """
        
        self.db = self.get_db()
        
        input_data = input_message.data
        
        embeddings = self.get_embeddings_model()
        
        response = {}

        operation = input_data["operation"]
        if operation not in ["write", "read"]:
            raise ValueError(f"Operation '{operation}' not supported")

        content = input_data["content"]
        
        if operation == "read":
            if not isinstance(content, str):
                raise ValueError(f"content(query) must be a string during read, got {type(content)}: {content}")
            if content == "":
                response["retrieved"] = [[""]]
            else:
                query = content
                query_result = self.db.similarity_search(query)
        
                response["retrieved"] = [doc.page_content for doc in query_result]

        elif operation == "write":
            if content != "":
                if not isinstance(content, list):
                    content = [content]
                documents = content
                self.db._collection.add(
                    ids=[str(uuid.uuid4()) for _ in range(len(documents))],
                    embeddings=embeddings.embed_documents(documents),
                    documents=documents
                )
                
            response["retrieved"] = ""

        reply = self.package_output_message(
            input_message = input_message,
            response = response
        )
        self.send_message(reply)
