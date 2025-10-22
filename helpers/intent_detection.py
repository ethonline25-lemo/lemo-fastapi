import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.config import llm_keys
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage
from prompts.intent_detection import intent_detection_prompt
from pydantic import BaseModel, Field
from typing import Literal, Optional, Dict, Any


# Define the output schema using Pydantic
class MessageForward(BaseModel):
    """Details about the user's message."""
    summary: str = Field(description="Short description of what the user wants")
    details: Dict[str, Any] = Field(default_factory=dict, description="Additional details")


class IntentOutput(BaseModel):
    """Structured output for intent detection."""
    intent: Literal["ask", "todo", "unknown"] = Field(description="The intent type")
    scope: Literal["current_page", "product", "cart", "order", "wishlist", "account", "chat_history", "unknown"] = Field(description="The scope of the intent")
    intent_confidence: float = Field(description="Confidence score between 0 and 1")
    message_forward: MessageForward = Field(description="Summary and details of the user message")
    follow_up_questions: str = Field(description="Suggested follow-up questions for the user")


# Get user input
user_input = input("Enter your input: ")

# Initialize the Gemini Model
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0.7,
    max_tokens=None,
    timeout=None,
    max_retries=2,
    api_key=llm_keys.gemini
)

# Apply structured output to the model
structured_llm = llm.with_structured_output(IntentOutput)

# Create messages with System (instruction) and User prompts
messages = [
    SystemMessage(content=intent_detection_prompt),
    HumanMessage(content=user_input)
]

# Invoke the model and get structured output
response = structured_llm.invoke(messages)

# Display the output
print("\n=== Structured Output ===")
print(f"Intent: {response.intent}")
print(f"Scope: {response.scope}")
print(f"Confidence: {response.intent_confidence}")
print(f"Summary: {response.message_forward.summary}")
print(f"Details: {response.message_forward.details}")
print(f"Follow-up: {response.follow_up_questions}")

# Convert to JSON dict
print("\n=== JSON Output ===")
import json
print(json.dumps(response.model_dump(), indent=2))
