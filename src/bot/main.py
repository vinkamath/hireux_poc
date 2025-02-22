import discord
import os
import dotenv
import logging

from . import agent
from .vectordb import load_index
from .chat import send_response_in_thread
from .conversation import ConversationManager, WorkflowState

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
    # Create a new thread for the conversation
    thread = await interaction.channel.create_thread(
        name=f"HireUX Chat with {interaction.user.name}",
        type=discord.ChannelType.public_thread
    )
    
    # Start a new conversation
    conversation_manager.start_conversation(thread.id, interaction.user.id)
    
    welcome_message = "Hello, I'm the HireUX bot and I'm happy to get you started. Would you like to get started with the job description?"
    await interaction.response.send_message(welcome_message, thread=thread)


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
        return

    logger.info(f"Received message in approved channel/thread: {message.content}")
    
    # Check if this is part of an active conversation
    if isinstance(message.channel, discord.Thread):
        conversation = conversation_manager.get_conversation(message.channel.id)
        if conversation and conversation.user_id == message.author.id:
            # Handle workflow states
            if conversation.state == WorkflowState.AWAITING_START_CONFIRMATION:
                response_lower = message.content.lower().strip()
                if response_lower in ['y', 'yes']:
                    conversation.state = WorkflowState.USER_ONBOARDING
                    await message.reply("Great! Let's start with the job description. Please paste your job description here.")
                else:
                    conversation.state = WorkflowState.COMPLETED
                    conversation_manager.end_conversation(message.channel.id)
                    await message.reply("No problem! You can still use this thread to chat with me, but we won't go through the guided workflow.")
                return

            elif conversation.state == WorkflowState.USER_ONBOARDING:
                # Handle user onboarding state
                query = message.content
                if len(query.split()) < 15:
                    await send_response_in_thread(message, agent.get_short_query_message())
                    return
                await agent.handle_candidate_request(message, query, index)
                return

    # Handle regular messages (non-workflow)
    query = message.content
    intent = await agent.classify_intent(query)

    if intent == "candidate-request":
        if len(query.split()) < 15:
            await send_response_in_thread(message, agent.get_short_query_message())
            return
        await agent.handle_candidate_request(message, query, index)
    else:
        await send_response_in_thread(message, agent.get_introductory_message())


client.run(DISCORD_TOKEN)