from django.conf import settings
import time

from langchain.docstore.document import Document
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
import chromadb

from fastydli.orders.models import ProductModel


__author__ = 'Ricardo'
__version__ = '0.1'


class VectorDBSingleton():

    __client = None
    __embeddings = None

    @classmethod
    def __get_connection(cls, embedding_function):
        """
        This method create our client
        """

        client = chromadb.PersistentClient(path="vector_db")

        client = Chroma(client=client, collection_name="dishes",
                        embedding_function=embedding_function)

        return client

    def __new__(cls, *args, **kwargs):

        if cls.__client == None:

            # making connection
            cls.__embeddings = OpenAIEmbeddings(
                api_key=settings.OPENAI_API_KEY)
            cls.__client = cls.__get_connection(cls.__embeddings)

        return cls.__client

    @classmethod
    async def create(cls):
        from asgiref.sync import sync_to_async
        docs = [Document(page_content=i.description, metadata={'name': i.name, 'price': float(i.price)}) for i in await sync_to_async(list)(ProductModel.objects.all())]
        await cls.__client.aadd_documents(documents=docs)
        print(await cls.search_similarity_procedure("hamburguesa"))

    @classmethod
    async def search_similarity_procedure(cls, text: str):
        """
        This method search the similarity in a text given inside a vectorial database

        :param text: an string beging our text to query
        :return: a list with our documents 
        """

        docs = await cls.__client.asimilarity_search(text, k=3)

        return docs
