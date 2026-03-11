import json
from ..memory import memory
from ..llm import generate_response

class UIDesigner:
    def __init__(self, user_id):
        self.user_id = user_id
        
    def generate_design_blueprint(self):
        # 1. Retrieve the Architect's strategy and user preferences from Mem0
        # This prevents hallucination by strictly relying on AI memory
        context = memory.search("What is the user's preferred theme, and what is the Architect's strategy?", user_id=self.user_id)
        facts = "\n".join([mem['content'] for mem in context.get('results', [])])
        
        # 2. Formulate the prompt for the LLM
        prompt = f"""
        You are the UI Designer for a portfolio generation system.
        Based on the following AI memory context involving user preferences and strategic decisions:
        
        {facts}
        
        Choose a layout and Bootstrap theme. 
        Output a rationale for why this design best represents the strategic goals.
        """
        
        # 3. Generate the response
        rationale = generate_response(prompt)
        
        # 4. Store the design rationale back into Mem0
        memory.add(
            messages=[{"role": "assistant", "content": f"UI Designer Design Decision: {rationale}"}],
            user_id=self.user_id
        )
        
        return rationale
