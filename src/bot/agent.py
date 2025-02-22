import logging
import asyncio
import discord
from llama_index.core import VectorStoreIndex, Settings, get_response_synthesizer, Settings
from llama_index.core.retrievers import VectorIndexRetriever
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.llms.openai import OpenAI

from .chat import send_response_in_thread
from .responses import BotResponses

# Load settings for LlamaIndex
Settings.llm = OpenAI(model="gpt-4o")
Settings.num_output = 512
Settings.context_window = 3900



logger = logging.getLogger("bot.agent")

async def classify_intent(query: str) -> str:
    """Classifies the intent of the user's query using an LLM."""
    prompt = f"""
    You are a helpful assistant that classifies user queries related to job descriptions and candidate matching.
    Classify the following query into one of the following categories:

    * candidate-request
    * Other

    Examples:

    Query: "Find me a UX designer with experience in Figma and user research."
    Category: candidate-request

    Query: "Hi there!"
    Category: Other

    Query: "{query}"
    Category:
    """
    try:
        llm = OpenAI(model="gpt-4o-mini")
        response = await asyncio.to_thread(llm.complete, prompt)
        intent = response.text.strip()
        logger.info(f"Classified intent: {intent} for query: {query}")

        # Validate the intent
        if intent not in ["candidate-request", "Other"]:
            logger.warning(f"Unexpected intent received: {intent}.  Defaulting to 'Other'.")
            return "Other"
        return intent

    except Exception as e:
        logger.error(f"Error during intent classification: {e}")
        return "Other"  # Default to "Other" on error

def get_short_query_message() -> str:
    return BotResponses.format_with_example(BotResponses.SHORT_DESCRIPTION)

def get_introductory_message() -> str:
    return BotResponses.INTRODUCTION.message

async def handle_candidate_request(message: discord.Message, query: str, index: VectorStoreIndex):
    """Handles a candidate request using the RAG pipeline."""
    try:
        # Construct a structured prompt (same as before, but now a separate function)
        job_description = query
        full_prompt = f"""
        You are a helpful assistant helping to match UX designers to job descriptions.

        Here is the job description:
        {job_description}

        Based on the provided job description, identify the top 3 UX designer candidates from our database who are the best fit.  For each candidate, provide:

        1.  Candidate name
        2.  A brief markdown formatted bullet summary (3-4 sentences max) explaining why they are a good match, referencing specific skills and experience from their portfolio. Use one sentence per bullet point.

        Be concise and specific.
        """

        # Set up retriever and query engine (same as before)
        retriever = VectorIndexRetriever(
            index=index,
            similarity_top_k=3,
        )
        nodes_with_scores = await asyncio.to_thread(retriever.retrieve, full_prompt)
        logger.info("Retrieved Nodes:")
        for node_with_score in nodes_with_scores:
            logger.info(f"Node Score: {node_with_score.score:.3f}")
            logger.info(f"Node Text:\n{node_with_score.node.get_content()}")
            logger.info("---")

        response_synthesizer = get_response_synthesizer()
        query_engine = RetrieverQueryEngine(
            retriever=retriever,
            response_synthesizer=response_synthesizer,
        )

        RAG_response = await asyncio.to_thread(query_engine.query, full_prompt)

        # Thread handling (same as before, but using a helper function)
        await send_response_in_thread(message, str(RAG_response))

    except Exception as e:
        await message.channel.send(f"An error occurred: {e}")
        logger.exception(f"Error during RAG processing: {e}")

