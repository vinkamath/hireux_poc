import chromadb  # Import chromadb
import discord
import asyncio
import os
import dotenv
import logging
from llama_index.core import VectorStoreIndex, Settings, get_response_synthesizer, StorageContext
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.retrievers import VectorIndexRetriever
from llama_index.llms.openai import OpenAI
from llama_index.vector_stores.chroma import ChromaVectorStore

dotenv.load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
CHROMA_DB_PATH = "chroma_db"  # Path to your ChromaDB database directory

intents = discord.Intents.all()
client = discord.Client(intents=intents)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("bot")


# Load settings for LlamaIndex
Settings.llm = OpenAI(model="gpt-4o", api_key=OPENAI_API_KEY)
Settings.num_output = 512
Settings.context_window = 3900


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


@client.event
async def on_ready():
    logger.info(f'We have logged in as {client.user}')
    global index  # Declare index as global to access it later
    index = await load_index() # Load index when bot is ready
    logger.info("Index loaded successfully.")

@client.event
async def on_message(message):
    if message.author == client.user:
        return  # Ignore messages from the bot itself

    # Respond only if tagged or using the prefix
    if client.user.mentioned_in(message):
        logger.info(f"Received message: {message.content}")
        # Remove the bot's mention and/or prefix from the query
        if client.user.mentioned_in(message):
            query = message.content.replace(f'<@{client.user.id}>', '').strip()
        else:
            query = message.content[5:]  # remove !rag prefix

        logger.info(f"Received RAG query: {query}")

        try:
            # Construct a structured prompt
            job_description = query  # The user's message IS the job description
            full_prompt = f"""
            You are a helpful assistant helping to match UX designers to job descriptions.

            Here is the job description:
            {job_description}

            Based on the provided job description, identify the top 3 UX designer candidates from our database who are the best fit.  For each candidate, provide:

            1.  Candidate name
            2.  A brief markdown formatted bullet summary (3-4 sentences max) explaining why they are a good match, referencing specific skills and experience from their portfolio. Use one sentence per bullet point.

            Be concise and specific.
            """

            # Set up retriever
            retriever = VectorIndexRetriever(
                index=index,
                similarity_top_k=3,
            )

            # Set up response synthesizer
            response_synthesizer = get_response_synthesizer()

            # Assemble query engine
            query_engine = RetrieverQueryEngine(
                retriever=retriever,
                response_synthesizer=response_synthesizer,
            )

            RAG_response = await asyncio.to_thread(query_engine.query, full_prompt) 

            # Check if the message is in a thread
            if isinstance(message.channel, discord.Thread):
                # Respond directly to the existing thread
                await message.channel.send(str(RAG_response))
                logger.info(f"Sent response to existing thread: {RAG_response}")
            else:
                # Create a new thread if not in a thread already
                try:  # Add try-except around thread creation
                    thread = await message.channel.create_thread(
                        name=f"RAG Response to {message.author.name}",
                        reason="Responding to RAG query",
                        type=discord.ChannelType.public_thread  # Explicitly set thread type
                    )
                    await thread.send(str(RAG_response))
                    logger.info(f"Created thread and sent response: {RAG_response}")
                except discord.errors.Forbidden as e:  # Handle permission errors specifically
                    await message.channel.send(f"I don't have permission to create threads or send messages in threads in this channel.  Please grant me the 'Create Public Threads' and 'Send Messages in Threads' permissions.")
                    logger.info(f"Permission error creating thread: {e}")
                except Exception as e:
                    await message.channel.send(f"An error occurred creating the thread: {e}")
                    logger.info(f"Error creating thread: {e}")

        except Exception as e:
            await message.channel.send(f"An error occurred: {e}")
            logger.info(f"Error during query processing: {e}")
client.run(DISCORD_TOKEN)