import redis
import numpy as np
from typing import List, Tuple
from core.config import REDIS_URL
import hashlib

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


# 1️⃣ Store a vector embedding for a URL
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


# 2️⃣ Search for similar URLs based on a query embedding
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


# 3️⃣ Delete a vector by URL
def delete_vector(url: str):
    """Delete a document vector from Redis."""
    url_hash = hashlib.md5(url.encode()).hexdigest()
    key = f"doc:{url_hash}"
    
    try:
        # Remove from the set
        r.srem("doc_keys", key)
        # Delete the hash
        result = r.delete(key)
        if result:
            return {"status": "success", "message": f"Deleted vector for {url}"}
        else:
            return {"status": "error", "message": f"No vector found for {url}"}
    except Exception as e:
        return {"status": "error", "message": f"Failed to delete vector: {str(e)}"}


# 4️⃣ Check storage stats
def get_storage_stats():
    """Get information about the stored documents."""
    try:
        doc_keys = r.smembers("doc_keys")
        count = len(doc_keys) if doc_keys else 0
        return {"status": "success", "document_count": count}
    except Exception as e:
        return {"status": "error", "message": str(e)}


# 5️⃣ List all stored documents
def list_all_documents():
    """List all stored document URLs."""
    try:
        doc_keys = r.smembers("doc_keys")
        urls = []
        
        for key in doc_keys:
            if isinstance(key, bytes):
                key = key.decode('utf-8')
            
            doc_data = r.hgetall(key)
            if doc_data and b'url' in doc_data:
                url = doc_data[b'url'].decode('utf-8') if isinstance(doc_data[b'url'], bytes) else doc_data[b'url']
                urls.append(url)
        
        return {"status": "success", "documents": urls, "count": len(urls)}
    except Exception as e:
        return {"status": "error", "message": str(e)}


# 6️⃣ Clear all documents (useful for testing)
def clear_all_documents():
    """Delete all stored documents."""
    try:
        doc_keys = r.smembers("doc_keys")
        
        if doc_keys:
            # Delete all document hashes
            for key in doc_keys:
                if isinstance(key, bytes):
                    key = key.decode('utf-8')
                r.delete(key)
            
            # Clear the set
            r.delete("doc_keys")
            
            return {"status": "success", "message": f"Deleted {len(doc_keys)} documents"}
        else:
            return {"status": "success", "message": "No documents to delete"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


# 7️⃣ Store page vector data (content chunks with embeddings)
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


# 8️⃣ Get relevant content for a URL based on query embedding
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