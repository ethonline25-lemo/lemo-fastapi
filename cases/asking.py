from context_retrivers.current_page_context import current_page_context
from context_retrivers.product_recommendation import product_recommendation
from core.config import llm_keys
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage
from prompts.currentpage_asking import currentpage_asking_prompt
from prompts.product_recommendation_prompt import product_recommendation_prompt
asking_llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0.7,
    max_tokens=None,
    timeout=None,
    max_retries=2,
    api_key=llm_keys.gemini
)

def current_page_asking(user_query: str, current_page_url: str):
    try:
        print(f"[LOG] current_page_asking called for URL: {current_page_url}")
        context = current_page_context(current_page_url, user_query)
        
        # Handle different context types
        if isinstance(context, list) and len(context) > 0:
            # Extract only the content from tuples (content, score)
            context_strings = [item[0] if isinstance(item, tuple) else item for item in context]
            context_text = "\n".join(context_strings)
            print(f"[LOG] Using {len(context_strings)} context chunks")
        elif isinstance(context, list) and len(context) == 0:
            context_text = "No relevant context found for this page."
            print("[WARNING] No context found for the page")
        else:
            context_text = str(context) if context else "No context available."
            print(f"[WARNING] Unexpected context type: {type(context)}")
        
        prompt = currentpage_asking_prompt(context_text)
        messages = [SystemMessage(content=prompt), HumanMessage(content=user_query)]
        response = asking_llm.invoke(messages)
        
        answer = response.content if response and response.content else "I couldn't generate a response. Please try again."
        print(f"[LOG] Generated answer: {answer[:100]}...")
        return answer
    
    except Exception as e:
        print(f"[ERROR] Error in current_page_asking: {e}")
        import traceback
        traceback.print_exc()
        return "I encountered an error while processing your question. Please try again."

def product_asking(user_query: str, domain: str):
    try:
        print(f"[LOG] product_asking called with domain: {domain}")
        recommendations = product_recommendation(domain, user_query)
        print(f"[LOG] Got {len(recommendations) if isinstance(recommendations, list) else 'unknown'} product recommendations")
        
        prompt = product_recommendation_prompt(user_query, recommendations)
        messages = [SystemMessage(content=prompt), HumanMessage(content=user_query)]
        response = asking_llm.invoke(messages)
        
        answer = response.content if response and response.content else "I couldn't generate a response. Please try again."
        print(f"[LOG] Generated answer: {answer[:100]}...")
        return answer
    
    except Exception as e:
        print(f"[ERROR] Error in product_asking: {e}")
        import traceback
        traceback.print_exc()
        return "I encountered an error while processing your product question. Please try again."

def chat_history_asking(user_query: str, session_id: str):
    print(f"[LOG] chat_history_asking called for session: {session_id}")
    # TODO: Implement chat history search
    return "I apologize, but I cannot search through chat history yet. Please ask about the current page you're viewing."

def asking(user_query: str, domain: str, current_page_url: str, scope: str, session_id: str):
    print(f"[LOG] asking() called with scope: {scope}")
    
    if scope == "current_page":
        return current_page_asking(user_query, current_page_url)
    elif scope == "product":
        print(f"[LOG] Product scope detected, using product_asking")
        return product_asking(user_query, domain)
    elif scope == "chat_history":
        return chat_history_asking(user_query, session_id)
    else:
        print(f"[WARNING] Unknown scope: {scope}, using current_page_asking as fallback")
        return current_page_asking(user_query, current_page_url)