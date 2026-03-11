import json
from ..memory import memory
from ..llm import generate_response

class CodeAuditor:
    def __init__(self, user_id):
        self.user_id = user_id
        
    def audit_code(self, generated_code):
        # Retrieve past developer sandbox feedback to ensure we don't repeat mistakes
        context = memory.search("Has the user provided any manual Sandbox feedback or previous corrections on code?", user_id=self.user_id)
        past_feedback = "\n".join([mem['content'] for mem in context.get('results', [])])
        
        prompt = f"""
        You are the Code Auditor. Review this generated code:
        {generated_code}
        
        Keep in mind these past user corrections from the Sandbox:
        {past_feedback}
        
        Provide validation feedback and point out syntax errors.
        """
        
        feedback = generate_response(prompt)
        
        # Store validation feedback into Mem0
        memory.add(
            messages=[{"role": "assistant", "content": f"Code Validation Result: {feedback}"}],
            user_id=self.user_id
        )
        
        return feedback
