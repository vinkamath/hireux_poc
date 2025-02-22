from enum import Enum
from dataclasses import dataclass
from typing import Dict, Optional
import asyncio

class WorkflowState(Enum):
    AWAITING_START_CONFIRMATION = "awaiting_start_confirmation"
    AWAITING_JOB_DESCRIPTION = "awaiting_job_description"
    AWAITING_CANDIDATE_LIST = "awaiting_candidate_list"
    USER_ONBOARDING = "user_onboarding"
    COMPLETED = "completed"

@dataclass
class Conversation:
    thread_id: int
    user_id: int
    state: WorkflowState
    timeout: float = 300.0  # 5 minutes default timeout

class ConversationManager:
    def __init__(self):
        self.active_conversations: Dict[int, Conversation] = {}  # thread_id -> Conversation

    def start_conversation(self, thread_id: int, user_id: int) -> Conversation:
        conversation = Conversation(
            thread_id=thread_id,
            user_id=user_id,
            state=WorkflowState.AWAITING_START_CONFIRMATION
        )
        self.active_conversations[thread_id] = conversation
        return conversation

    def get_conversation(self, thread_id: int) -> Optional[Conversation]:
        return self.active_conversations.get(thread_id)

    def end_conversation(self, thread_id: int):
        if thread_id in self.active_conversations:
            del self.active_conversations[thread_id] 