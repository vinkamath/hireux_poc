import logging
import chromadb
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.core import VectorStoreIndex, StorageContext

logger = logging.getLogger("bot.vectordb")

CHROMA_DB_PATH = "chroma_db"  # Path to your ChromaDB database directory

async def load_index():
    # Load Chroma client and collection
    chroma_client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
    chroma_collection = chroma_client.get_collection("ux_portfolios")

    # Set up ChromaVectorStore
    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)

    # Load the index from the existing vector store
    index = VectorStoreIndex.from_vector_store(
        vector_store, storage_context=storage_context
    )

    return index

