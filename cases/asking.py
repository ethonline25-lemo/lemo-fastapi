from context_retrivers.current_page_context import current_page_context
from core.config import llm_keys
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage
from prompts.currentpage_asking import currentpage_asking_prompt
asking_llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0.7,
    max_tokens=None,
    timeout=None,
    max_retries=2,
    api_key=llm_keys.gemini
)


def current_page_asking(user_query: str, current_page_url: str):
    context = current_page_context(current_page_url, user_query)
    
    # Handle different context types
    if isinstance(context, list) and len(context) > 0:
        # Extract only the content from tuples (content, score)
        context_strings = [item[0] if isinstance(item, tuple) else item for item in context]
        context_text = "\n".join(context_strings)
    elif isinstance(context, list) and len(context) == 0:
        context_text = "No relevant context found for this page."
    else:
        context_text = str(context) if context else "No context available."
    
    prompt = currentpage_asking_prompt(context_text)
    messages = [SystemMessage(content=prompt), HumanMessage(content=user_query)]
    response = asking_llm.invoke(messages)
    return response.content

def product_asking(user_query: str, domain: str):
    pass

def chat_history_asking(user_query: str,session_id: str):
    pass

def asking(user_query: str, domain: str, current_page_url: str,scope: str,session_id: str):
    if scope == "current_page":
        return current_page_asking(user_query, current_page_url)
    elif scope == "product":
        return product_asking(user_query, domain)
    elif scope == "chat_history":
        return chat_history_asking(user_query, session_id)
    else:
        return "Unknown scope"