import discord
import logging

logger = logging.getLogger("bot.chat")

MAX_MSG_LEN = 2000 # Max length of a message in Discord
MSG_PREVIEW_LEN = 500 # How much of the message to show in a preview

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
