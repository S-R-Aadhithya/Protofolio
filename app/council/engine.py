from .agents import TechLead, Designer, ProductManager, Chairman
from .memory import MemoryManager

class CouncilEngine:
    def __init__(self):
        self.tech_lead = TechLead()
        self.designer = Designer()
        self.pm = ProductManager()
        self.chairman = Chairman()
        self.memory = MemoryManager()

    def deliberate(self, user_id, user_input):
        print(f"DEBUG: Starting deliberation for user {user_id} with goal: {user_input}")
        
        # Retrieve RAG Context from Mem0
        print("DEBUG: Retrieving memory chunks...")
        context = self.memory.retrieve_chunks(user_id, user_input)
        print(f"DEBUG: Retrieved context: {len(context)} chars")
        
        # Stage 1: Opinions
        print("DEBUG: Stage 1 - Fetching expert opinions...")
        opinions = [
            self.tech_lead.get_opinion(context, user_input),
            self.designer.get_opinion(context, user_input),
            self.pm.get_opinion(context, user_input)
        ]
        print(f"DEBUG: Stage 1 COMPLETE. Opinions received: {len(opinions)}")
        
        # Stage 2: Reviews
        print("DEBUG: Stage 2 - Peer reviewing opinions...")
        reviews = [
            self.tech_lead.review(context, opinions),
            self.designer.review(context, opinions),
            self.pm.review(context, opinions)
        ]
        print(f"DEBUG: Stage 2 COMPLETE. Reviews received: {len(reviews)}")
        
        # Format deliberations for synthesis
        deliberation_history = "--- INITIAL OPINIONS ---\n"
        deliberation_history += f"Tech Lead Original: {opinions[0]}\n\n"
        deliberation_history += f"Designer Original: {opinions[1]}\n\n"
        deliberation_history += f"PM Original: {opinions[2]}\n\n"
        
        deliberation_history += "--- PEER REVIEWS & CRITIQUES ---\n"
        deliberation_history += f"Tech Lead Review: {reviews[0]}\n\n"
        deliberation_history += f"Designer Review: {reviews[1]}\n\n"
        deliberation_history += f"PM Review: {reviews[2]}\n\n"
            
        # Stage 3: Synthesis
        final_blueprint_str = self.chairman.synthesize(user_input, deliberation_history)
        
        # Try to parse JSON from synthesis
        try:
            # Simple extract JSON if it's wrapped in markers
            import json
            json_str = final_blueprint_str
            if "```json" in json_str:
                json_str = json_str.split("```json")[1].split("```")[0]
            elif "```" in json_str:
                json_str = json_str.split("```")[1].split("```")[0]
            blueprint = json.loads(json_str)
        except Exception:
            blueprint = {"error": "Failed to parse synthesis", "raw": final_blueprint_str}

        return {
            "deliberation": deliberation_history,
            "blueprint": blueprint
        }
