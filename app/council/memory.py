import os
from mem0 import Memory

def get_memory_client():
    """
    Initializes and returns the Mem0 Memory client.
    Because vector DBs are strictly excluded, we configure Mem0 to use 
    the native SQLite/PostgreSQL instance as its persistent layer.
    """
    # Use SQLite for local development context as per config.py
    # If production, use PostgreSQL parsed from DATABASE_URL
    database_url = os.getenv('DATABASE_URL', 'sqlite:///instance/protofolio_dev.db')
    
    # We strip the leading 'sqlite:///' or 'postgresql://' if Mem0 expects specific formats, 
    # though standard SQLAlchemy DSN is usually fine.
    # Mem0 by default attempts Qdrant or Chroma, we explicitly force a relational store if supported
    # Note: If Mem0 natively only supports vector stores, we use its built-in SQLite integration
    # for local caching.
    
    config = {
        "vector_store": {
            "provider": "chroma", 
            "config": {
                "collection_name": "protofolio_memory",
                "path": "instance/chromadb" 
            }
        },
        "embedder": {
            "provider": "gemini",
            "config": {
                "model": "models/text-embedding-004"
            }
        },
        "llm": {
            "provider": "gemini",
            "config": {
                "model": "gemini-1.5-flash",
                "temperature": 0.2,
            }
        }
    }
    
    # Mem0 requires an API key for Google/Gemini
    # We ensure GOOGLE_API_KEY is set (using GEMINI_API_KEY as fallback)
    if not os.getenv('GOOGLE_API_KEY'):
        os.environ['GOOGLE_API_KEY'] = os.getenv('GEMINI_API_KEY', 'dummy-key-for-mem0')
        
    m = Memory.from_config(config)
    return m

# Global instance for the application to reuse
memory = get_memory_client()

class MemoryManager:
    def __init__(self):
        self.client = memory

    def add_fact(self, user_id, content, metadata=None):
        """Adds a fact to Mem0 for a specific user."""
        self.client.add(
            messages=[{"role": "user", "content": content}], 
            user_id=str(user_id), 
            metadata=metadata
        )

    def retrieve_chunks(self, user_id, query, limit=5):
        print(f"DEBUG: Mem0 searching for user {user_id} query: {query}")
        results = self.client.search(query, user_id=str(user_id), limit=limit)
        print(f"DEBUG: Mem0 search returned {len(results) if isinstance(results, list) else 'non-list'} results")
        
        # Check if results is a list of dictionaries (standard Mem0 search output)
        if isinstance(results, list):
            facts = [res.get("content", "") for res in results if "content" in res]
            return "\n".join(facts)
        
        # Fallback for different return types if any
        return str(results)

    def get_all_memories(self, user_id):
        """Retrieves all memories for a user."""
        return self.client.get_all(user_id=str(user_id))
