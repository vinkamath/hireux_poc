import os
import dotenv
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, Settings, StorageContext
from llama_index.llms.openai import OpenAI
from llama_index.vector_stores.chroma import ChromaVectorStore
import chromadb  # Import chromadb
import logging

dotenv.load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
CHROMA_DB_PATH = "chroma_db"  # Path to your ChromaDB database directory

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger("ingest")

def ingest_data():
    Settings.llm = OpenAI(model="gpt-4o", api_key=OPENAI_API_KEY)  # Ensure you have your OPENAI_API_KEY set
    Settings.embed_model = OpenAIEmbedding(model="text-embedding-3-small", api_key=OPENAI_API_KEY)
    Settings.node_parser = SentenceSplitter(chunk_size=512, chunk_overlap=128 )
    Settings.num_output = 512
    Settings.context_window = 3900
    logger.info("Settings loaded successfully.")

    # Load documents
    reader = SimpleDirectoryReader(input_dir="data/output/portfolio", recursive=True)
    documents = reader.load_data()

    # Create Chroma client and collection
    chroma_client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
    chroma_collection = chroma_client.get_or_create_collection("ux_portfolios")

    # Set up ChromaVectorStore
    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)

    # Create the index
    VectorStoreIndex.from_documents(
        documents, storage_context=storage_context
    )
    logging.info("Data ingestion and indexing complete.")


if __name__ == "__main__":
    ingest_data()