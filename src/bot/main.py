# src/bot.py
import discord
import os
import dotenv
import logging

from vectordb import load_index
import agent

dotenv.load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.all()
client = discord.Client(intents=intents)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("bot")


async def send_response_in_thread(message: discord.Message, response_text: str):
    """Sends the response in a thread, handling thread creation and errors."""
    try:
        if isinstance(message.channel, discord.Thread):
            await message.channel.send(response_text)
            logger.info(f"Sent response to existing thread: {response_text}")
        else:
            thread = await message.channel.create_thread(
                name=f"RAG Response to {message.author.name}",
                reason="Responding to RAG query",
                type=discord.ChannelType.public_thread
            )
            await thread.send(response_text)
            logger.info(f"Created thread and sent response: {response_text}")
    except discord.errors.Forbidden as e:
        await message.channel.send(
            "I don't have permission to create threads or send messages in threads in this channel.  "
            "Please grant me the 'Create Public Threads' and 'Send Messages in Threads' permissions."
        )
        logger.error(f"Permission error creating thread: {e}")
    except Exception as e:
        await message.channel.send(f"An error occurred creating the thread: {e}")
        logger.exception(f"Error creating thread: {e}")


@client.event
async def on_ready():
    logger.info(f'We have logged in as {client.user}')
    global index
    index = await load_index()
    logger.info("Index loaded successfully.")


@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if client.user.mentioned_in(message):
        logger.info(f"Received message: {message.content}")
        query = message.content.replace(f'<@{client.user.id}>', '').strip()


        # Intent classification
        intent = await agent.classify_intent(query)

        if intent == "candidate-request":
            # Length check
            if len(query.split()) < 15:  # Using word count as a proxy for length
                await send_response_in_thread(message, agent.get_short_query_message())
                return
            await agent.handle_candidate_request(message, query, index)
        else:
            await send_response_in_thread(message, agent.get_introductory_message())


client.run(DISCORD_TOKEN)