import logging
import os
from discord import Message
from .conversation import WorkflowState
from .responses import BotResponses
from . import chat
from src.common.utility import process_pdf
import csv

logger = logging.getLogger("bot.handlers")

async def handle_start_confirmation(message: Message, conversation, conversation_manager) -> None:
    """Handle the start confirmation state."""
    response_lower = message.content.lower().strip()
    if response_lower in ['y', 'yes', 'sure', 'ok', 'okay']:
        conversation.state = WorkflowState.AWAITING_JOB_DESCRIPTION
        await message.reply(BotResponses.format_with_example(BotResponses.JOB_DESCRIPTION_REQUEST))
    else:
        conversation.state = WorkflowState.COMPLETED
        conversation_manager.end_conversation(message.channel.id)
        await message.reply(BotResponses.WORKFLOW_EXIT.message)

async def handle_job_description(message: Message, conversation) -> None:
    """Handle the job description state."""
    job_description = None
    
    # Check for PDF attachment
    if message.attachments and message.attachments[0].filename.lower().endswith('.pdf'):
        attachment = message.attachments[0]
        try:
            await attachment.save(f"temp_{message.id}.pdf")
            job_description = await process_pdf(f"temp_{message.id}.pdf")
            os.remove(f"temp_{message.id}.pdf")
            logger.info(f"Removed temp file: temp_{message.id}.pdf")
            
            if not job_description:
                await message.reply(BotResponses.PDF_PROCESSING_ERROR.message)
                return
            
            if len(job_description) > chat.MSG_PREVIEW_LEN:
                job_description = job_description[:chat.MSG_PREVIEW_LEN - 3] + "..."
            await message.reply(job_description)
            
        except Exception as e:
            logger.error(f"Error processing PDF: {e}")
            await message.reply(BotResponses.PDF_PROCESSING_ERROR.message)
            return
    else:
        job_description = message.content

    # Validate job description length
    if len(job_description.split()) < 15:
        await message.reply(BotResponses.format_with_example(BotResponses.SHORT_DESCRIPTION))
        return

    # Move to next state
    conversation.state = WorkflowState.AWAITING_CANDIDATE_LIST
    await message.reply(BotResponses.format_with_example(BotResponses.CANDIDATE_LIST_REQUEST))

async def handle_candidate_list(message: Message, conversation) -> None:
    """Handle the candidate list state."""
    if not message.attachments or not message.attachments[0].filename.lower().endswith('.csv'):
        await message.reply("Please upload a CSV file with two columns: candidate names and URLs.")
        return
    
    try:
        attachment = message.attachments[0]
        await attachment.save(f"temp_{message.id}.csv")
        
        candidates = {}
        errors = []
        
        with open(f"temp_{message.id}.csv", 'r', encoding='utf-8') as file:
            reader = csv.reader(file)
            first_row = next(reader, None)
            
            # Process CSV data
            is_header = _check_if_header(first_row)
            rows = [first_row] if not is_header else []
            rows.extend(reader)
            
            candidates, errors = _process_csv_rows(rows)
        
        # Clean up temp file
        os.remove(f"temp_{message.id}.csv")
        
        await _send_candidate_processing_response(message, candidates, errors)
        
        if candidates:
            conversation.candidates = candidates
            conversation.state = WorkflowState.COMPLETED
            
    except Exception as e:
        logger.error(f"Error processing CSV: {e}")
        await message.reply("An error occurred while processing the CSV file. Please ensure the file is properly formatted.")
        if os.path.exists(f"temp_{message.id}.csv"):
            os.remove(f"temp_{message.id}.csv")

def _check_if_header(first_row) -> bool:
    """Check if the first row is a header."""
    if first_row and len(first_row) == 2:
        url = first_row[1].strip()
        return not url.startswith(('http://', 'https://', 'www.'))
    return True

def _process_csv_rows(rows):
    """Process CSV rows and return candidates and errors."""
    candidates = {}
    errors = []
    
    for row_num, row in enumerate(rows, start=1):
        if len(row) != 2:
            errors.append(f"Row {row_num}: Expected 2 columns, found {len(row)}")
            continue
            
        name, url = row
        name = name.strip()
        url = url.strip()
        
        # Validate name
        name_parts = name.split()
        if len(name_parts) < 2:
            errors.append(f"Row {row_num}: Invalid name format - {name}")
            continue
        
        # Create standardized name key
        key = ''.join(word.capitalize() for word in name_parts)
        
        # Validate URL
        if not url.startswith(('http://', 'https://', 'www.')):
            errors.append(f"Row {row_num}: Invalid URL format - {url}")
            continue
        
        # Standardize URL format
        if url.startswith('www.'):
            url = 'http://' + url
        
        candidates[key] = url
    
    return candidates, errors

async def _send_candidate_processing_response(message, candidates, errors):
    """Send appropriate response based on candidate processing results."""
    if not candidates:
        await message.reply("❌ No valid candidates could be processed from the CSV. Please ensure:\n"
                         "• The file has exactly 2 columns\n"
                         "• Names are in 'First Last' format\n"
                         "• URLs start with http://, https:// or www.")
        if errors:
            await message.reply("Errors found:\n" + "\n".join(errors))
    else:
        success_msg = f"✅ Successfully processed {len(candidates)} candidate{'s' if len(candidates) != 1 else ''}"
        if errors:
            success_msg += f"\n️❌ ({len(errors)} error{'s' if len(errors) != 1 else ''} encountered)"
        await message.reply(success_msg) 