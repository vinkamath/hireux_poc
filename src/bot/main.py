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
                response_lower = message.content.lower().strip()
                if response_lower in ['y', 'yes']:
                    conversation.state = WorkflowState.AWAITING_JOB_DESCRIPTION
                    await message.reply(BotResponses.format_with_example(BotResponses.JOB_DESCRIPTION_REQUEST))
                else:
                    conversation.state = WorkflowState.COMPLETED
                    conversation_manager.end_conversation(message.channel.id)
                    await message.reply(BotResponses.WORKFLOW_EXIT.message)
                return

            elif conversation.state == WorkflowState.AWAITING_JOB_DESCRIPTION:
                # Check for PDF attachment
                if message.attachments and message.attachments[0].filename.lower().endswith('.pdf'):
                    # Handle PDF upload
                    attachment = message.attachments[0]
                    try:
                        # Download the PDF
                        await attachment.save(f"temp_{message.id}.pdf")
                        # Process the PDF (you'll need to implement this function)
                        job_description = await process_pdf(f"temp_{message.id}.pdf")
                        # Clean up
                        os.remove(f"temp_{message.id}.pdf")
                        logger.info(f"Removed temp file: temp_{message.id}.pdf")
                        
                        if not job_description:
                            await message.reply(BotResponses.PDF_PROCESSING_ERROR.message)
                            return
                        else:
                            # Truncate job description if it exceeds preview length
                            if len(job_description) > chat.MSG_PREVIEW_LEN:
                                job_description = job_description[:chat.MSG_PREVIEW_LEN - 3] + "..."
                            await message.reply(job_description)
                            
                    except Exception as e:
                        logger.error(f"Error processing PDF: {e}")
                        await message.reply(BotResponses.PDF_PROCESSING_ERROR.message)
                        return
                else:
                    # Handle text input
                    job_description = message.content

                # Process the job description
                if len(job_description.split()) < 15:
                    await message.reply(BotResponses.format_with_example(BotResponses.SHORT_DESCRIPTION))
                    return

                # Move to next state and process
                conversation.state = WorkflowState.AWAITING_CANDIDATE_LIST
                await message.reply(BotResponses.format_with_example(BotResponses.CANDIDATE_LIST_REQUEST))
                return

            elif conversation.state == WorkflowState.AWAITING_CANDIDATE_LIST:
                # Check for CSV attachment
                if not message.attachments or not message.attachments[0].filename.lower().endswith('.csv'):
                    await message.reply("Please upload a CSV file with two columns: candidate names and URLs.")
                    return
                
                try:
                    # Download and process the CSV
                    attachment = message.attachments[0]
                    await attachment.save(f"temp_{message.id}.csv")
                    
                    import csv
                    
                    candidates = {}
                    errors = []
                    
                    with open(f"temp_{message.id}.csv", 'r', encoding='utf-8') as file:
                        reader = csv.reader(file)
                        first_row = next(reader, None)
                        
                        # Check if first row is a header or data
                        is_header = True
                        if first_row and len(first_row) == 2:
                            url = first_row[1].strip()
                            if url.startswith(('http://', 'https://', 'www.')):
                                is_header = False
                        
                        # Process rows, including first row if it's data
                        rows = [first_row] if not is_header else []
                        rows.extend(reader)
                        
                        for row_num, row in enumerate(rows, start=1):  # Start at 1 since we're handling all data rows
                            if len(row) != 2:
                                errors.append(f"Row {row_num}: Expected 2 columns, found {len(row)}")
                                continue
                                
                            name, url = row
                            
                            # Clean and validate name
                            name = name.strip()
                            name_parts = name.split()
                            if len(name_parts) < 2:
                                errors.append(f"Row {row_num}: Invalid name format - {name}")
                                continue
                            
                            # Create standardized name key (FirstnameLastname)
                            key = ''.join(word.capitalize() for word in name_parts)
                            
                            # Basic URL validation
                            url = url.strip()
                            if not url.startswith(('http://', 'https://', 'www.')):
                                errors.append(f"Row {row_num}: Invalid URL format - {url}")
                                continue
                            
                            # Ensure www. URLs start with http://
                            if url.startswith('www.'):
                                url = 'http://' + url
                            
                            candidates[key] = url
                    
                    # Clean up temp file
                    os.remove(f"temp_{message.id}.csv")
                    
                    if not candidates:
                        await message.reply("❌ No valid candidates could be processed from the CSV. Please ensure:\n"
                                         "• The file has exactly 2 columns\n"
                                         "• Names are in 'First Last' format\n"
                                         "• URLs start with http://, https:// or www.")
                        if errors:
                            await message.reply("Errors found:\n" + "\n".join(errors))
                    else:
                        # Store candidates in conversation state for later use
                        conversation.candidates = candidates
                        
                        success_msg = f"✅ Successfully processed {len(candidates)} candidate{'s' if len(candidates) != 1 else ''}"
                        if errors:
                            success_msg += f"\n️❌ ({len(errors)} error{'s' if len(errors) != 1 else ''} encountered)"
                        
                        await message.reply(success_msg)
                        # Move to next state
                        conversation.state = WorkflowState.COMPLETED
                        
                except Exception as e:
                    logger.error(f"Error processing CSV: {e}")
                    await message.reply("An error occurred while processing the CSV file. Please ensure the file is properly formatted.")
                    if os.path.exists(f"temp_{message.id}.csv"):
                        os.remove(f"temp_{message.id}.csv")
                return

            elif conversation.state == WorkflowState.USER_ONBOARDING:
                # TBD: Handle further interaction in the onboarding state
                query = message.content
                await agent.handle_candidate_request(message, query, index)
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