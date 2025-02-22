import discord
import os
import dotenv
import logging

from . import agent
from .vectordb import load_index
from . import chat
from .conversation import ConversationManager, WorkflowState
from src.common.utility import process_pdf
from .responses import BotResponses
from .handlers import (
    handle_start_confirmation,
    handle_job_description,
    handle_candidate_list
)

dotenv.load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
# Add approved channel IDs as integers
APPROVED_CHANNELS = [
    int(channel_id) for channel_id in os.getenv("APPROVED_CHANNELS", "").split(",")
    if channel_id
]

intents = discord.Intents.all()
client = discord.Client(intents=intents)
tree = discord.app_commands.CommandTree(client)

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("bot")

# Add after other global variables
conversation_manager = ConversationManager()

@tree.command(name="start", description="Start a conversation with the HireUX bot")
async def start(interaction: discord.Interaction):
    try:
        thread = None
        
        # If we're in a thread, use it
        if isinstance(interaction.channel, discord.Thread):
            thread = interaction.channel
        else:
            # Create a new thread for the conversation
            thread = await interaction.channel.create_thread(
                name=f"Onboarding Chat with {interaction.user.name}",
                type=discord.ChannelType.public_thread
            )
        
        # Start a new conversation
        conversation_manager.start_conversation(thread.id, interaction.user.id)
        
        # First, respond to the interaction
        await interaction.response.send_message("Starting conversation...", ephemeral=True)
        
        # Then send the welcome message in the thread
        await thread.send(BotResponses.WELCOME.message)
        logger.info(f"Started new conversation in thread {thread.id} for user {interaction.user.name}")
    except Exception as e:
        logger.error(f"Error in start command: {e}")
        await interaction.response.send_message("Sorry, something went wrong while starting the conversation.", ephemeral=True)


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

    # Check if message is in an approved channel or thread
    if not (message.channel.id in APPROVED_CHANNELS or 
            (isinstance(message.channel, discord.Thread) and 
             message.channel.parent_id in APPROVED_CHANNELS)):
        logger.warning(f"Received message in non-approved channel/thread: {message.content}")
        return

    logger.info(f"Received message in approved channel/thread: {message.content}")
    
    # Check if this is part of an active conversation
    if isinstance(message.channel, discord.Thread):
        conversation = conversation_manager.get_conversation(message.channel.id)
        # Only allow the original user who started the conversation to interact with it
        if conversation and conversation.user_id == message.author.id:
            # Handle workflow states
            if conversation.state == WorkflowState.AWAITING_START_CONFIRMATION:
                await handle_start_confirmation(message, conversation, conversation_manager)
                return

            elif conversation.state == WorkflowState.AWAITING_JOB_DESCRIPTION:
                await handle_job_description(message, conversation)
                return

            elif conversation.state == WorkflowState.AWAITING_CANDIDATE_LIST:
                await handle_candidate_list(message, conversation)
                return

            elif conversation.state == WorkflowState.USER_ONBOARDING:
                await agent.handle_candidate_request(message, message.content, index)
                return

    # Handle regular messages (non-workflow)
    query = message.content
    if query.lower() == 'help':
        await message.reply(BotResponses.HELP.message)
        return

    intent = await agent.classify_intent(query)

    if intent == "candidate-request":
        if len(query.split()) < 15:
            await chat.send_response_in_thread(message, agent.get_short_query_message())
            return
        await agent.handle_candidate_request(message, query, index)
    else:
        await chat.send_response_in_thread(message, agent.get_introductory_message())


client.run(DISCORD_TOKEN)