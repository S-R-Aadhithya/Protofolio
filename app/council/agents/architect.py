import json
from ..memory import memory
from ..llm import generate_response # Assuming a shared LLM wrapper

class ContentArchitect:
    def __init__(self, user_id):
        self.user_id = user_id
        
    def generate_strategy(self):
        # 1. Retrieve all contextual memory for this user from Mem0
        context = memory.search("What is the user's background, skills, and target job goal?", user_id=self.user_id)
        
        # 2. Extract facts from the memory response
        # Mem0 search returns a dict with 'results' containing the memory blocks
        facts = "\n".join([mem['content'] for mem in context.get('results', [])])
        
        # 3. Formulate the prompt for the LLM
        prompt = f"""
        You are the Content Architect for a portfolio generation system.
        Based on the following ingested memory about the user:
        
        {facts}
        
        Decide which projects and skills should be highlighted to maximize appeal for their target role.
        Return a strategic summary.
        """
        
        # 4. Generate the response (Placeholder for actual LLM call)
        strategy = generate_response(prompt)
        
        # 5. Store the decision rationale back into Mem0 so other agents can reference it
        memory.add(
            messages=[{"role": "assistant", "content": f"Content Architect Strategic Decision: {strategy}"}],
            user_id=self.user_id
        )
        
        return strategy
