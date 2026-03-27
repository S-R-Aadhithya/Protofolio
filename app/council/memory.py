import os
from mem0 import Memory

def get_memory_client():
    """
    Initializes and returns the Mem0 Memory client.
    Handles missing API keys gracefully for CI environments.
    """
    api_key = os.getenv('GOOGLE_API_KEY') or os.getenv('GEMINI_API_KEY')
    
    # If no key is found, or it's a dummy placeholder, return None to signal mock mode
    if not api_key or "dummy" in api_key.lower():
        print("WARNING: No valid Gemini API key found. Mem0 will operate in mock mode.")
        return None

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
                "model": "models/text-embedding-004",
                "api_key": api_key
            }
        },
        "llm": {
            "provider": "gemini",
            "config": {
                "model": "gemini-1.5-flash",
                "temperature": 0.2,
                "api_key": api_key
            }
        }
    }
    
    try:
        m = Memory.from_config(config)
        return m
    except Exception as e:
        print(f"WARNING: Failed to initialize Mem0 (likely library version or API error): {e}. Falling back to mock mode.")
        return None

# Global instance for the application to reuse
memory = get_memory_client()

class MemoryManager:
    def __init__(self):
        self.client = memory

    def add_fact(self, user_id, content, metadata=None):
        """Adds a fact to Mem0 for a specific user with fallback."""
        if not self.client:
            print(f"INFO: Mem0 in mock mode. Skipping add_fact for user {user_id}.")
            return

        try:
            self.client.add(
                messages=[{"role": "user", "content": content}], 
                user_id=str(user_id), 
                metadata=metadata
            )
        except Exception as e:
            print(f"WARNING: Mem0 add_fact failed: {e}. skipping...")

    def retrieve_chunks(self, user_id, query, limit=5):
        """Retrieves memories for a user with robust fallback."""
        if self.client:
            print(f"DEBUG: Mem0 searching for user {user_id} query: {query}")
            try:
                results = self.client.search(query, user_id=str(user_id), limit=limit)
                if isinstance(results, list):
                    facts = [res.get("content", "") for res in results if "content" in res]
                    return "\n".join(facts)
            except Exception as e:
                print(f"WARNING: Mem0 search failed (likely API key): {e}. Falling back to mock context.")
        
        # Deterministic mock context based on query to provide variability during experiments
        q_lower = query.lower()
        if "front" in q_lower or "react" in q_lower:
            return "Mock context: User likes React, CSS animations, and modern UI design."
        elif "back" in q_lower or "python" in q_lower:
            return "Mock context: User emphasizes Python, SQL optimization, and API performance."
        elif "data" in q_lower or "ml" in q_lower:
            return "Mock context: User focuses on data engineering, Spark, and model evaluation."
        
        return "Mock context: General developer background with core engineering proficiency."

    def get_all_memories(self, user_id):
        """Retrieves all memories for a user."""
        if not self.client:
            return []
        try:
            return self.client.get_all(user_id=str(user_id))
        except Exception:
            return []
