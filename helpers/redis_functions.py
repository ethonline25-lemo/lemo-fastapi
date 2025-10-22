import redis
import numpy as np
from typing import List, Tuple, Dict, Any, Optional
from core.config import REDIS_URL
import hashlib
import json
from datetime import datetime

VECTOR_DIM = 384  # embedding dimension

# Connect to Redis
r = redis.Redis.from_url(REDIS_URL, decode_responses=False)


# Create a simple index (no RediSearch needed - just for compatibility)
def create_redis_index():
    """
    Create a simple index tracking system (no RediSearch required).
    This is a workaround for Redis instances without RediSearch module.
    """
    try:
        # Just create a set to track all document keys
        # This doesn't require RediSearch
        print("[INFO] Using simple vector storage (no RediSearch module required)")
        return {"status": "success", "message": "Simple index initialized"}
    except Exception as e:
        print(f"Error initializing storage: {e}")
        return {"status": "error", "message": str(e)}


#  Store a vector embedding for a URL
def store_vector(url: str, embedding: List[float]):
    """Store a document URL with its vector embedding in Redis."""
    if len(embedding) != VECTOR_DIM:
        raise ValueError(f"Embedding dimension mismatch. Expected {VECTOR_DIM}, got {len(embedding)}")
    
    # Create a unique hash for the URL
    url_hash = hashlib.md5(url.encode()).hexdigest()
    key = f"doc:{url_hash}"
    
    # Convert embedding to bytes
    emb_array = np.array(embedding, dtype=np.float32).tobytes()

    try:
        # Store the document
        r.hset(key, mapping={
            "url": url,
            "embedding": emb_array
        })
        
        # Add to the set of all documents for easy retrieval
        r.sadd("doc_keys", key)
        
        return {"status": "success", "message": f"Stored vector for {url}"}
    except Exception as e:
        return {"status": "error", "message": f"Failed to store vector: {str(e)}"}


# Search for similar URLs based on a query embedding
def search_similar(query_embedding: List[float], top_k: int = 5) -> List[Tuple[str, float]]:
    """
    Search for similar documents using cosine similarity.
    This implementation doesn't require RediSearch - it manually computes similarities.
    """
    if len(query_embedding) != VECTOR_DIM:
        raise ValueError(f"Query embedding dimension mismatch. Expected {VECTOR_DIM}, got {len(query_embedding)}")

    try:
        # Get all document keys
        doc_keys = r.smembers("doc_keys")
        
        if not doc_keys:
            print("[WARNING] No documents found in Redis")
            return []
        
        print(f"[LOG] Searching through {len(doc_keys)} documents")
        
        query_vector = np.array(query_embedding, dtype=np.float32)
        query_norm = np.linalg.norm(query_vector)
        
        similarities = []
        
        # Calculate cosine similarity for each document
        for key in doc_keys:
            try:
                # Decode key if it's bytes
                if isinstance(key, bytes):
                    key = key.decode('utf-8')
                
                # Get the embedding and URL
                doc_data = r.hgetall(key)
                
                if not doc_data or b'embedding' not in doc_data:
                    continue
                
                # Extract embedding
                emb_bytes = doc_data[b'embedding']
                doc_vector = np.frombuffer(emb_bytes, dtype=np.float32)
                
                # Extract URL
                url = doc_data[b'url'].decode('utf-8') if isinstance(doc_data[b'url'], bytes) else doc_data[b'url']
                
                # Calculate cosine similarity
                doc_norm = np.linalg.norm(doc_vector)
                
                if doc_norm == 0 or query_norm == 0:
                    similarity = 0.0
                else:
                    similarity = np.dot(query_vector, doc_vector) / (query_norm * doc_norm)
                
                similarities.append((url, float(similarity)))
                
            except Exception as e:
                print(f"[WARNING] Error processing document {key}: {e}")
                continue
        
        # Sort by similarity (highest first) and return top_k
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        print(f"[LOG] Found {len(similarities)} valid similarities")
        if similarities:
            print(f"[LOG] Top similarity score: {similarities[0][1]:.4f}")
        
        return similarities[:top_k]
    
    except Exception as e:
        print(f"[ERROR] Search failed: {e}")
        import traceback
        traceback.print_exc()
        return []


# Store page vector data (content chunks with embeddings)
def store_page_vector(url: str, content: str, embedding: List[float]):
    """
    Store page content with its vector embedding.
    Multiple chunks can be stored for the same URL.
    
    Args:
        url: The page URL
        content: The text content/chunk
        embedding: Vector embedding of the content
        
    Returns:
        Dict with status and message
    """
    if len(embedding) != VECTOR_DIM:
        raise ValueError(f"Embedding dimension mismatch. Expected {VECTOR_DIM}, got {len(embedding)}")
    
    try:
        # Create a unique key for this content chunk
        # Combine URL and content hash to allow multiple chunks per URL
        content_hash = hashlib.md5(content.encode()).hexdigest()
        url_hash = hashlib.md5(url.encode()).hexdigest()
        chunk_key = f"page:{url_hash}:{content_hash}"
        
        # Convert embedding to bytes
        emb_array = np.array(embedding, dtype=np.float32).tobytes()
        
        # Store the page content chunk
        r.hset(chunk_key, mapping={
            "url": url,
            "content": content,
            "embedding": emb_array
        })
        
        # Add to the set of all page chunks
        r.sadd("page_keys", chunk_key)
        
        # Also track which chunks belong to this URL
        r.sadd(f"url_chunks:{url_hash}", chunk_key)
        
        return {"status": "success", "message": f"Stored page vector for {url}"}
    except Exception as e:
        return {"status": "error", "message": f"Failed to store page vector: {str(e)}"}


# Get relevant content for a URL based on query embedding
def get_relevant_content(url: str, query_embedding: List[float], top_k: int = 3) -> List[Tuple[str, float]]:
    """
    Get the most relevant content chunks for a specific URL based on query similarity.
    
    Args:
        url: The page URL to search within
        query_embedding: Vector embedding of the query
        top_k: Number of most relevant chunks to return
        
    Returns:
        List of tuples (content, similarity_score) ordered by relevance
    """
    if len(query_embedding) != VECTOR_DIM:
        raise ValueError(f"Query embedding dimension mismatch. Expected {VECTOR_DIM}, got {len(query_embedding)}")
    
    try:
        # Get all chunks for this URL
        url_hash = hashlib.md5(url.encode()).hexdigest()
        chunk_keys = r.smembers(f"url_chunks:{url_hash}")
        
        if not chunk_keys:
            print(f"[WARNING] No content chunks found for URL: {url}")
            return []
        
        print(f"[LOG] Searching through {len(chunk_keys)} content chunks for {url}")
        
        query_vector = np.array(query_embedding, dtype=np.float32)
        query_norm = np.linalg.norm(query_vector)
        
        similarities = []
        
        # Calculate cosine similarity for each chunk
        for key in chunk_keys:
            try:
                # Decode key if it's bytes
                if isinstance(key, bytes):
                    key = key.decode('utf-8')
                
                # Get the chunk data
                chunk_data = r.hgetall(key)
                
                if not chunk_data or b'embedding' not in chunk_data or b'content' not in chunk_data:
                    continue
                
                # Extract embedding
                emb_bytes = chunk_data[b'embedding']
                chunk_vector = np.frombuffer(emb_bytes, dtype=np.float32)
                
                # Extract content
                content = chunk_data[b'content'].decode('utf-8') if isinstance(chunk_data[b'content'], bytes) else chunk_data[b'content']
                
                # Calculate cosine similarity
                chunk_norm = np.linalg.norm(chunk_vector)
                
                if chunk_norm == 0 or query_norm == 0:
                    similarity = 0.0
                else:
                    similarity = np.dot(query_vector, chunk_vector) / (query_norm * chunk_norm)
                
                similarities.append((content, float(similarity)))
                
            except Exception as e:
                print(f"[WARNING] Error processing chunk {key}: {e}")
                continue
        
        # Sort by similarity (highest first) and return top_k
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        print(f"[LOG] Found {len(similarities)} valid content chunks")
        if similarities:
            print(f"[LOG] Top similarity score: {similarities[0][1]:.4f}")
        
        return similarities[:top_k]
    
    except Exception as e:
        print(f"[ERROR] Failed to get relevant content: {e}")
        import traceback
        traceback.print_exc()
        return []


# Get chat history based on session_id
def get_chat_history(session_id: str) -> Optional[List[Dict[str, Any]]]:
    """
    Get chat history for a session.
    
    Args:
        session_id: The session identifier
        
    Returns:
        List of message dictionaries or None if not found
    """
    try:
        key = f"chat:{session_id}:messages"
        messages_json = r.get(key)
        
        if not messages_json:
            print(f"[WARNING] No chat history found for session: {session_id}")
            return None
        
        # Decode if bytes
        if isinstance(messages_json, bytes):
            messages_json = messages_json.decode('utf-8')
        
        messages = json.loads(messages_json)
        print(f"[LOG] Retrieved {len(messages)} messages for session {session_id}")
        return messages
    
    except Exception as e:
        print(f"[ERROR] Failed to get chat history: {e}")
        return None


# Store chat history based on session_id
def store_chat_history(session_id: str, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Store complete chat history for a session.
    
    Args:
        session_id: The session identifier
        messages: List of message dictionaries with keys:
                 - message: str
                 - message_type: str (user/assistant/system)
                 - detected_intent: Optional[str]
                 - created_at: Optional[str] (auto-added if not present)
        
    Returns:
        Dict with status and message
    """
    try:
        # Add timestamps if not present
        for msg in messages:
            if "created_at" not in msg or not msg["created_at"]:
                msg["created_at"] = datetime.utcnow().isoformat()
        
        key = f"chat:{session_id}:messages"
        messages_json = json.dumps(messages)
        
        r.set(key, messages_json)
        
        # Update session last activity
        session_key = f"chat:{session_id}:last_activity"
        r.set(session_key, datetime.utcnow().isoformat())
        
        print(f"[LOG] Stored {len(messages)} messages for session {session_id}")
        return {"status": "success", "message": f"Stored {len(messages)} messages", "session_id": session_id}
    
    except Exception as e:
        print(f"[ERROR] Failed to store chat history: {e}")
        return {"status": "error", "message": f"Failed to store chat history: {str(e)}"}


# Add a message to chat
def add_message_to_chat(
    session_id: str,
    message: str,
    message_type: str,
    detected_intent: Optional[str] = None
) -> Dict[str, Any]:
    """
    Add a single message to chat history.
    
    Args:
        session_id: The session identifier
        message: Message content
        message_type: Type of message (user/assistant/system)
        detected_intent: Detected intent (optional)
        
    Returns:
        Dict with status, message, and the added message object
    """
    try:
        # Validate message_type
        if message_type not in ["user", "assistant", "system"]:
            return {"status": "error", "message": f"Invalid message_type: {message_type}. Must be user/assistant/system"}
        
        # Get existing messages or create new list
        messages = get_chat_history(session_id) or []
        
        # Create new message
        new_message = {
            "message": message,
            "message_type": message_type,
            "detected_intent": detected_intent,
            "created_at": datetime.utcnow().isoformat()
        }
        
        # Append and save
        messages.append(new_message)
        result = store_chat_history(session_id, messages)
        
        if result["status"] == "success":
            print(f"[LOG] Added {message_type} message to session {session_id}")
            return {"status": "success", "message": "Message added", "added_message": new_message}
        else:
            return result
    
    except Exception as e:
        print(f"[ERROR] Failed to add message: {e}")
        return {"status": "error", "message": f"Failed to add message: {str(e)}"}