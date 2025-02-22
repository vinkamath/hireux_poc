# src/bot.py
import discord
import os
import dotenv
import logging
from discord import app_commands

from . import agent
from .vectordb import load_index
from .chat import send_response_in_thread

dotenv.load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
# Add approved channel IDs as integers
APPROVED_CHANNELS = [
    int(channel_id) for channel_id in os.getenv("APPROVED_CHANNELS", "").split(",")
    if channel_id
]

intents = discord.Intents.all()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("bot")


@tree.command(name="start", description="Start a conversation with the HireUX bot")
async def start(interaction: discord.Interaction):
    welcome_message = "Hello, I'm the HireUX bot and I'm happy to get you started. Would you like to get started with the job description?"
    await interaction.response.send_message(welcome_message)


@client.event
async def on_ready():
    logger.info(f'We have logged in as {client.user}')
    global index
    index = await load_index()
    # Sync the command tree
    await tree.sync()
    logger.info("Index loaded successfully and commands synced.")


@client.event
async def on_message(message):
    if message.author == client.user:
        return

    # Check if message is in an approved channel
    if message.channel.id in APPROVED_CHANNELS:
        logger.info(f"Received message in approved channel: {message.content}")
        query = message.content

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