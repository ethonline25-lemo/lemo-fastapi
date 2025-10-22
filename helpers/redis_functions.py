# import redis
# from redis.commands.search.field import VectorField, TextField, NumericField, TagField
# from redis.commands.search.indexDefinition import IndexDefinition, IndexType
# from redis.commands.search.query import Query
# import numpy as np
# import json
# from datetime import datetime
# from typing import List, Dict, Optional, Any
# from enum import Enum


# class MessageType(str, Enum):
#     USER = "user"
#     ASSISTANT = "assistant"
#     SYSTEM = "system"


# class RedisHelper:
#     def __init__(
#         self,
#         host: str = 'localhost',
#         port: int = 6379,
#         db: int = 0,
#         password: Optional[str] = None,
#         vector_dim: int = 384,
#         decode_responses: bool = True
#     ):
#         """
#         Initialize Redis connection and setup vector index
        
#         Args:
#             host: Redis host
#             port: Redis port
#             db: Redis database number
#             password: Redis password (if required)
#             vector_dim: Dimension of embedding vectors
#             decode_responses: Whether to decode responses
#         """
#         self.client = redis.Redis(
#             host=host,
#             port=port,
#             db=db,
#             password=password,
#             decode_responses=decode_responses
#         )
#         self.vector_dim = vector_dim
#         self.chunks_index_name = "chunks_idx"
#         self._initialize_vector_index()
    
#     def _initialize_vector_index(self):
#         """Initialize vector search index for chunks"""
#         try:
#             self.client.ft(self.chunks_index_name).info()
#         except:
#             schema = (
#                 TextField("content"),
#                 VectorField(
#                     "embedding",
#                     "FLAT",
#                     {
#                         "TYPE": "FLOAT32",
#                         "DIM": self.vector_dim,
#                         "DISTANCE_METRIC": "COSINE"
#                     }
#                 ),
#                 NumericField("timestamp"),
#                 TextField("metadata")
#             )
#             self.client.ft(self.chunks_index_name).create_index(
#                 fields=schema,
#                 definition=IndexDefinition(
#                     prefix=["chunk:"],
#                     index_type=IndexType.HASH
#                 )
#             )
    
#     # ==========================================
#     # CHAT SESSION FUNCTIONS
#     # ==========================================
    
#     def create_chat_session(
#         self,
#         session_id: str,
#         user_id: Optional[str] = None,
#         current_url: Optional[str] = None,
#         current_domain: Optional[str] = None
#     ) -> Dict[str, Any]:
#         """
#         Create a new chat session
        
#         Args:
#             session_id: Unique session identifier
#             user_id: User identifier
#             current_url: Current URL of the session
#             current_domain: Current domain of the session
            
#         Returns:
#             Dict with session details
#         """
#         session_key = f"session:{session_id}"
#         now = datetime.utcnow().isoformat()
        
#         session_data = {
#             "session_id": session_id,
#             "user_id": user_id or "",
#             "current_url": current_url or "",
#             "current_domain": current_domain or "",
#             "created_at": now,
#             "last_activity": now
#         }
        
#         self.client.hset(session_key, mapping=session_data)
#         return session_data
    
#     def get_chat_session(self, session_id: str) -> Optional[Dict[str, Any]]:
#         """
#         Get chat session details
        
#         Args:
#             session_id: Session identifier
            
#         Returns:
#             Session data or None if not found
#         """
#         session_key = f"session:{session_id}"
#         session_data = self.client.hgetall(session_key)
        
#         if not session_data:
#             return None
        
#         return session_data
    
#     def update_session_activity(self, session_id: str):
#         """
#         Update last activity timestamp for a session
        
#         Args:
#             session_id: Session identifier
#         """
#         session_key = f"session:{session_id}"
#         self.client.hset(
#             session_key,
#             "last_activity",
#             datetime.utcnow().isoformat()
#         )
    
#     # ==========================================
#     # CHAT HISTORY FUNCTIONS
#     # ==========================================
    
#     def save_chat_history(
#         self,
#         session_id: str,
#         messages: List[Dict[str, Any]]
#     ) -> Dict[str, Any]:
#         """
#         Save complete chat history for a session
        
#         Args:
#             session_id: Session identifier
#             messages: List of message dictionaries with keys:
#                      - message: str
#                      - message_type: str (user/assistant/system)
#                      - user_id: Optional[str]
#                      - detected_intent: Optional[str]
#                      - created_at: Optional[str]
                     
#         Returns:
#             Status dictionary
#         """
#         # Update session activity
#         self.update_session_activity(session_id)
        
#         # Save messages list
#         messages_key = f"session:{session_id}:messages"
        
#         # Add timestamps if not present
#         for msg in messages:
#             if "created_at" not in msg or not msg["created_at"]:
#                 msg["created_at"] = datetime.utcnow().isoformat()
        
#         self.client.set(messages_key, json.dumps(messages))
        
#         return {
#             "status": "success",
#             "session_id": session_id,
#             "message_count": len(messages)
#         }
    
#     def get_chat_history(self, session_id: str) -> Optional[List[Dict[str, Any]]]:
#         """
#         Get chat history for a session
        
#         Args:
#             session_id: Session identifier
            
#         Returns:
#             List of messages or None if not found
#         """
#         messages_key = f"session:{session_id}:messages"
#         messages_json = self.client.get(messages_key)
        
#         if not messages_json:
#             return None
        
#         return json.loads(messages_json)
    
#     def add_message_to_chat(
#         self,
#         session_id: str,
#         message: str,
#         message_type: MessageType,
#         user_id: Optional[str] = None,
#         detected_intent: Optional[str] = None
#     ) -> Dict[str, Any]:
#         """
#         Add a single message to chat history
        
#         Args:
#             session_id: Session identifier
#             message: Message content
#             message_type: Type of message (user/assistant/system)
#             user_id: User identifier
#             detected_intent: Detected intent (optional)
            
#         Returns:
#             The added message dictionary
#         """
#         # Get existing messages or create new list
#         messages = self.get_chat_history(session_id) or []
        
#         # Create new message
#         new_message = {
#             "message": message,
#             "message_type": message_type.value if isinstance(message_type, MessageType) else message_type,
#             "user_id": user_id,
#             "detected_intent": detected_intent,
#             "created_at": datetime.utcnow().isoformat()
#         }
        
#         # Append and save
#         messages.append(new_message)
#         self.save_chat_history(session_id, messages)
        
#         return new_message
    
#     def delete_chat_history(self, session_id: str) -> bool:
#         """
#         Delete chat history and session
        
#         Args:
#             session_id: Session identifier
            
#         Returns:
#             True if deleted, False if not found
#         """
#         session_key = f"session:{session_id}"
#         messages_key = f"session:{session_id}:messages"
        
#         deleted = self.client.delete(session_key, messages_key)
#         return deleted > 0
    
#     # ==========================================
#     # VECTOR CHUNKS FUNCTIONS
#     # ==========================================
    
#     def add_chunk(
#         self,
#         content: str,
#         embedding: List[float],
#         metadata: Optional[Dict[str, Any]] = None
#     ) -> str:
#         """
#         Add a single chunk with its vector embedding
        
#         Args:
#             content: Text content of the chunk
#             embedding: Vector embedding (must match vector_dim)
#             metadata: Optional metadata dictionary
            
#         Returns:
#             Chunk ID
#         """
#         if len(embedding) != self.vector_dim:
#             raise ValueError(
#                 f"Embedding dimension {len(embedding)} doesn't match "
#                 f"expected dimension {self.vector_dim}"
#             )
        
#         chunk_id = f"chunk:{self.client.incr('chunk_counter')}"
        
#         # Convert embedding to bytes
#         embedding_bytes = np.array(embedding, dtype=np.float32).tobytes()
        
#         chunk_data = {
#             "content": content,
#             "embedding": embedding_bytes,
#             "timestamp": datetime.utcnow().timestamp(),
#             "metadata": json.dumps(metadata or {})
#         }
        
#         self.client.hset(chunk_id, mapping=chunk_data)
#         return chunk_id
    
#     def add_chunks_batch(
#         self,
#         chunks: List[Dict[str, Any]]
#     ) -> List[str]:
#         """
#         Add multiple chunks at once
        
#         Args:
#             chunks: List of dictionaries with keys:
#                    - content: str
#                    - embedding: List[float]
#                    - metadata: Optional[Dict]
                   
#         Returns:
#             List of chunk IDs
#         """
#         chunk_ids = []
#         pipe = self.client.pipeline()
        
#         for chunk in chunks:
#             chunk_id = f"chunk:{self.client.incr('chunk_counter')}"
            
#             if len(chunk["embedding"]) != self.vector_dim:
#                 raise ValueError(
#                     f"Embedding dimension {len(chunk['embedding'])} doesn't match "
#                     f"expected dimension {self.vector_dim}"
#                 )
            
#             embedding_bytes = np.array(
#                 chunk["embedding"],
#                 dtype=np.float32
#             ).tobytes()
            
#             chunk_data = {
#                 "content": chunk["content"],
#                 "embedding": embedding_bytes,
#                 "timestamp": datetime.utcnow().timestamp(),
#                 "metadata": json.dumps(chunk.get("metadata", {}))
#             }
            
#             pipe.hset(chunk_id, mapping=chunk_data)
#             chunk_ids.append(chunk_id)
        
#         pipe.execute()
#         return chunk_ids
    
#     def get_relevant_chunks(
#         self,
#         query_embedding: List[float],
#         top_k: int = 5,
#         min_similarity: float = 0.0
#     ) -> List[Dict[str, Any]]:
#         """
#         Search for relevant chunks using similarity search
        
#         Args:
#             query_embedding: Query vector embedding
#             top_k: Number of results to return
#             min_similarity: Minimum similarity threshold (0-1)
            
#         Returns:
#             List of relevant chunks with similarity scores
#         """
#         if len(query_embedding) != self.vector_dim:
#             raise ValueError(
#                 f"Query embedding dimension {len(query_embedding)} doesn't match "
#                 f"expected dimension {self.vector_dim}"
#             )
        
#         # Convert query embedding to bytes
#         query_bytes = np.array(query_embedding, dtype=np.float32).tobytes()
        
#         # Create KNN query
#         q = Query(
#             f"*=>[KNN {top_k} @embedding $vec AS score]"
#         ).sort_by("score").return_fields(
#             "content", "metadata", "timestamp", "score"
#         ).dialect(2)
        
#         # Execute search
#         results = self.client.ft(self.chunks_index_name).search(
#             q,
#             query_params={"vec": query_bytes}
#         )
        
#         # Format results
#         formatted_results = []
#         for doc in results.docs:
#             # Convert distance to similarity (cosine distance: 0 = identical, 2 = opposite)
#             similarity = 1 - (float(doc.score) / 2)
            
#             if similarity >= min_similarity:
#                 formatted_results.append({
#                     "chunk_id": doc.id,
#                     "content": doc.content,
#                     "metadata": json.loads(doc.metadata),
#                     "timestamp": float(doc.timestamp),
#                     "similarity_score": similarity
#                 })
        
#         return formatted_results
    
#     def get_chunk(self, chunk_id: str) -> Optional[Dict[str, Any]]:
#         """
#         Get a specific chunk by ID
        
#         Args:
#             chunk_id: Chunk identifier
            
#         Returns:
#             Chunk data or None if not found
#         """
#         if not chunk_id.startswith("chunk:"):
#             chunk_id = f"chunk:{chunk_id}"
        
#         chunk_data = self.client.hgetall(chunk_id)
        
#         if not chunk_data:
#             return None
        
#         return {
#             "chunk_id": chunk_id,
#             "content": chunk_data["content"],
#             "metadata": json.loads(chunk_data.get("metadata", "{}")),
#             "timestamp": float(chunk_data.get("timestamp", 0))
#         }
    
#     # ==========================================
#     # USER PREFERENCES FUNCTIONS
#     # ==========================================
    
#     def save_user_preference(
#         self,
#         user_id: str,
#         preference_text: str
#     ) -> Dict[str, Any]:
#         """
#         Save or update user preference
        
#         Args:
#             user_id: User identifier
#             preference_text: User preference text
            
#         Returns:
#             Preference data dictionary
#         """
#         preference_key = f"user:{user_id}:preferences"
#         now = datetime.utcnow().isoformat()
        
#         # Check if preference exists
#         existing = self.client.hgetall(preference_key)
        
#         preference_data = {
#             "user_id": user_id,
#             "preference_text": preference_text,
#             "created_at": existing.get("created_at", now),
#             "updated_at": now
#         }
        
#         self.client.hset(preference_key, mapping=preference_data)
#         return preference_data
    
#     def get_user_preference(self, user_id: str) -> Optional[Dict[str, Any]]:
#         """
#         Get user preference
        
#         Args:
#             user_id: User identifier
            
#         Returns:
#             Preference data or None if not found
#         """
#         preference_key = f"user:{user_id}:preferences"
#         preference_data = self.client.hgetall(preference_key)
        
#         if not preference_data:
#             return None
        
#         return preference_data
    
#     def delete_user_preference(self, user_id: str) -> bool:
#         """
#         Delete user preference
        
#         Args:
#             user_id: User identifier
            
#         Returns:
#             True if deleted, False if not found
#         """
#         preference_key = f"user:{user_id}:preferences"
#         deleted = self.client.delete(preference_key)
#         return deleted > 0
    
#     # ==========================================
#     # UTILITY FUNCTIONS
#     # ==========================================
    
#     def ping(self) -> bool:
#         """
#         Check Redis connection
        
#         Returns:
#             True if connected, False otherwise
#         """
#         try:
#             return self.client.ping()
#         except:
#             return False
    
#     def flush_all(self):
#         """
#         DANGER: Delete all data in Redis database
#         Use only for testing/development
#         """
#         self.client.flushdb()
    
#     def get_session_count(self) -> int:
#         """Get total number of sessions"""
#         return len(self.client.keys("session:*"))
    
#     def get_chunk_count(self) -> int:
#         """Get total number of chunks"""
#         return len(self.client.keys("chunk:*"))


import redis
import numpy as np
from typing import List, Tuple, Optional

# Redis configuration
REDIS_CONFIG = {
    "host": "172.19.132.45",
    "port": 6379,
    "db": 0,
    "password": None
}

VECTOR_DIM = 384  # embedding dimension

# Connect to Redis
r = redis.Redis(**REDIS_CONFIG)

# Ensure the index exists (HNSW vector index)
def create_redis_index():
    from redis.commands.search.field import VectorField, TextField
    from redis.commands.search.indexDefinition import IndexDefinition, IndexType
    from redis.commands.search import Search

    search = Search(r)
    existing_indexes = [idx.name for idx in search.list()]
    if "doc_index" not in existing_indexes:
        r.ft("doc_index").create_index(
            [
                TextField("url"),
                VectorField("embedding", "HNSW", {
                    "TYPE": "FLOAT32",
                    "DIM": VECTOR_DIM,
                    "DISTANCE_METRIC": "COSINE"
                })
            ],
            definition=IndexDefinition(prefix=["doc:"], index_type=IndexType.HASH)
        )


# 1️⃣ Store a vector embedding for a URL
def store_vector(url: str, embedding: List[float]):
    if len(embedding) != VECTOR_DIM:
        raise ValueError(f"Embedding dimension mismatch. Expected {VECTOR_DIM}, got {len(embedding)}")
    
    key = f"doc:{url}"
    emb_array = np.array(embedding, dtype=np.float32).tobytes()

    r.hset(key, mapping={
        "url": url,
        "embedding": emb_array
    })
    return {"status": "success", "message": f"Stored vector for {url}"}


# 2️⃣ Search for similar URLs based on a query embedding
def search_similar(query_embedding: List[float], top_k: int = 5) -> List[Tuple[str, float]]:
    if len(query_embedding) != VECTOR_DIM:
        raise ValueError(f"Query embedding dimension mismatch. Expected {VECTOR_DIM}, got {len(query_embedding)}")

    query_vector = np.array(query_embedding, dtype=np.float32).tobytes()

    query = f"*=>[KNN {top_k} @embedding $vec_param AS score]"
    params_dict = {"vec_param": query_vector}

    results = r.ft("doc_index").search(
        query,
        query_params=params_dict,
        sort_by="score",
        return_fields=["url", "score"],
        dialect=2
    )

    return [(doc.url, float(doc.score)) for doc in results.docs]
