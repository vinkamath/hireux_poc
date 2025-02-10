import discord
import asyncio
import os
import dotenv
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader
from llama_index.llms.openai import OpenAI
from llama_index.core import Settings

Settings.llm = OpenAI(model="gpt-4o")  # Ensure you have your OPENAI_API_KEY set
Settings.embed_model = OpenAIEmbedding(model="text-embedding-3-small")
Settings.node_parser = SentenceSplitter(chunk_size=512, chunk_overlap=20)
Settings.num_output = 512
Settings.context_window = 3900


# Load documents and build the index (same as your original code)
documents = SimpleDirectoryReader(input_dir="data/input", recursive=True).load_data()
index = VectorStoreIndex.from_documents(documents)
query_engine = index.as_query_engine()


dotenv.load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
intents = discord.Intents.all()
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')

@client.event
async def on_message(message):
    print(f"Received message: {message.content}")
    if message.author == client.user:
        return  # Ignore messages from the bot itself

    # Respond only if tagged or using the prefix
    if client.user.mentioned_in(message) or message.content.startswith("!rag"):
        # Remove the bot's mention and/or prefix from the query
        if client.user.mentioned_in(message):
            query = message.content.replace(f'<@{client.user.id}>', '').strip()
        else:
            query = message.content[5:] # remove !rag prefix

        print(f"Received RAG query: {query}")

        try:
            RAG_response = query_engine.query(query)

            # Check if the message was sent in a thread. If so respond in that thread. Otherwise create one.
            if message.channel.type == discord.ChannelType.public_thread:
                await message.channel.send(str(RAG_response))
                print(f"Sent response in thread: {RAG_response}")
            else:
                # Create a new thread
                try:
                    thread = await message.channel.create_thread(
                        name=f"RAG Response to {message.author.name}",
                        reason="Responding to RAG query"
                    )
                    await thread.send(str(RAG_response))
                    print(f"Created thread and sent response: {RAG_response}")

                except Exception as e:
                    await message.channel.send(f"Could not create thread: {e}")  # Fallback if thread creation fails
                    await message.channel.send(str(RAG_response)) # Send response in channel as fallback

        except Exception as e:
            await message.channel.send(f"An error occurred: {e}")
            print(f"Error during query processing: {e}")
    else:
        await message.channel.send("Please start your message with '!rag' to use the RAG model.")

client.run(DISCORD_TOKEN)