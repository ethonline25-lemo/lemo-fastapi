import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.config import llm_keys
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.output_parsers.json import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_core.messages import HumanMessage


instruction_prompt = '''You are the Lemo Intent Decision Agent.
Your task is to analyze a user's natural language input and output a single JSON object that captures what the user is trying to do. You are NOT to decide what should be done next or how to execute it — only interpret user intent.

OUTPUT SCHEMA:
{
  "intent": "ask|todo|unknown",
  "scope": "current_page|product|cart|order|wishlist|account|chat_history|unknown",
  "intent_confidence": number,
  "message_forward": {
    "summary": "short description of what the user wants",
    "details": {}
  },
  "follow_up_questions": string
}

RULES:
1. Output only valid JSON. No markdown, commentary, or code fences.
2. intent: classify whether the user is asking for info (ask), performing an action (todo), or unclear (unknown).
3. scope: choose the main domain of the request (product, current_page, cart, order, wishlist, account, chat_history, unknown).
4. message_forward.summary: concise, human-readable summary of what the user wants.
5. message_forward.details: structured fields relevant to that summary (e.g., action type, product name, filters, size, etc.). Don't assume anything by your own assumption, only use the information provided in the user's input and the context of the conversation.
6. If not enough info, fill unknowns with null or ask short follow-up questions.
7. Confidence is a float 0–1.
8. Do not assume product IDs or prices.
9. Be minimal and precise.
10. Follow up questions should be add if and only if the user's instruction is too unclear to be understood by the model, and its a string of questions that the user could ask to get more information or to clarify the intent.

EXAMPLES:
{"intent":"ask","scope":"order","intent_confidence":0.94,"message_forward":{"summary":"user wants to know order status","details":{"action":"get_order_status","order_id":null}},"follow_up_questions":""}

{"intent":"todo","scope":"cart","intent_confidence":0.96,"message_forward":{"summary":"user wants to add a product to cart","details":{"action":"add_to_cart","product_reference":"current_page","size":"M"}},"follow_up_questions":""}

{"intent":"ask","scope":"product","intent_confidence":0.9,"message_forward":{"summary":"user wants to search for red shirts under 1000","details":{"category":"shirt","color":"red","price_max":1000}},"follow_up_questions":""}
'''

user_input = input("Enter your input: ")

parser = JsonOutputParser()
format_instructions = parser.get_format_instructions()

prompt_template = PromptTemplate(
    input_variables=["instruction", "format_instructions", "user_input"],
    template="""{instruction}

Return output that matches exactly the JSON schema described below. Do not include any commentary, explanation, or markdown—only JSON.

{format_instructions}

User input:
{user_input}
"""
)

prompt = prompt_template.format(
    instruction=instruction_prompt,
    format_instructions=format_instructions,
    user_input=user_input
)

model = ChatGoogleGenerativeAI(
    model="gemma-3-1b-it",
    temperature=0,
    api_key=llm_keys.gemini,
    max_retries=None
)

response = model.invoke([HumanMessage(content=prompt)])
raw_text = response.content.strip()

try:
    parsed = parser.parse(raw_text)
except Exception as e:
    print("Failed to parse model output. Raw response:")
    print(raw_text)
    raise e

print(parsed)
