import os
from dotenv import load_dotenv
load_dotenv() # Load your fresh GROQ_API_KEY from .env

from app.council.engine import CouncilEngine

def run_direct():
    print(f"Loaded GROQ API Key: {os.getenv('GROQ_API_KEY')[:8]}...")
    print("Starting the AI Council Engine internally... Please hold tight!")
    
    engine = CouncilEngine()
    
    # Let's bypass the API and just simulate a 1-to-1 backend call using the mock user id 1
    # We will use "Senior UI/UX Designer focusing on building highly engaging Figma prototypes."
    result = engine.deliberate(
        1,
        "Senior UI/UX Designer focusing on building highly engaging Figma prototypes."
    )
    
    print("\n--- DONE! ---\n")
    print(result.get("deliberation"))
    
if __name__ == "__main__":
    run_direct()
