from dataclasses import dataclass
from typing import Dict, List

@dataclass
class ResponseTemplate:
    message: str
    examples: List[str] = None

class BotResponses:
    # Onboarding workflow responses
    WELCOME = ResponseTemplate(
        "Hello, I'm the HireUX bot and I'm happy to get you started. Would you like to get started with the job description?"
    )
    
    JOB_DESCRIPTION_REQUEST = ResponseTemplate(
        message="Great! Please either paste your job description here or upload it as a PDF file.",
        examples=[
            "We are looking for a Senior UX Designer to lead the design of our new mobile app. "
            "The ideal candidate will have 5+ years of experience in UX design, with a strong portfolio showcasing mobile app design. "
            "They should be proficient in Figma, Sketch, and user research methodologies."
        ]
    )
    
    WORKFLOW_EXIT = ResponseTemplate(
        "No problem! You can still use this thread to chat with me, but we won't go through the guided workflow."
    )

    # Error messages
    PDF_PROCESSING_ERROR = ResponseTemplate(
        "Sorry, I had trouble processing that PDF. Could you please paste the job description as text instead?"
    )
    
    SHORT_DESCRIPTION = ResponseTemplate(
        message="That job description seems a bit short. Could you provide more details?",
        examples=[
            "Consider including:\n"
            "• Required years of experience\n"
            "• Key responsibilities\n"
            "• Required skills and tools\n"
            "• Project types or industry focus"
        ]
    )

    # General responses
    INTRODUCTION = ResponseTemplate(
        "👋 Hi there! I'm a bot designed to help match UX designers to job descriptions.\n\n"
        "You can say /start to begin the onboarding process. Or say help to get a list of commands.\n\n"
    )

    HELP = ResponseTemplate(
        "Here are the available commands:\n"
        "• /start - Begin the job description workflow\n"
        "• /help - Show this help message"
    )

    @classmethod
    def format_with_example(cls, template: ResponseTemplate) -> str:
        """Formats a response template with examples if they exist."""
        if not template.examples:
            return template.message
            
        example_text = "\n\nFor example:\n" + "\n\n".join(template.examples)
        return template.message + example_text 