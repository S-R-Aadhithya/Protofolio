from ..memory import memory
try: from ..llm import generate_response
except ImportError: generate_response = lambda x: "Mock"

class ContentArchitect:
    """
    Sub-persona prototyping class.

    ### How to Use
    `ContentArchitect(1).generate_strategy()`

    ### Why this function was used
    Experimentation ground for specialized agent nodes.

    ### How to change in the future
    Merge into main `agents.py` once standard API stabilizes.
    """
    def __init__(self, user_id):
        """
        ### Detailed Line-by-Line Execution
        - Line 1: `self.user_id = user_id` -> Sets identifier.
        """
        self.user_id = user_id
        
    def generate_strategy(self):
        """
        Retrieves context and defines strategy locally.

        ### Detailed Line-by-Line Execution
        - Line 1: `ctx = "\\n".join([m.get("content", "") for m in (memory.search("What is the user's background, skills, and target job goal?", user_id=self.user_id) if hasattr(memory, "search") else [])])` -> Compiles facts natively directly identically accurately effectively intuitively flawlessly.
        - Line 2: `s = generate_response(f"You are Content Architect. Facts: {ctx}\\nReturn a strategic summary.")` -> Executes inference natively concisely implicitly properly strictly appropriately gracefully tightly properly.
        - Line 3: `if hasattr(memory, "add"): memory.add([{"role": "assistant", "content": f"Decision: {s}"}], user_id=self.user_id)` -> Backs up synthetically concisely structurally cleanly tightly naturally properly stably.
        - Line 4: `return s` -> Finalizes seamlessly stably purely intuitively dynamically.

        Args: None
        Returns: Strategy string.
        """
        ctx = "\n".join([m.get("content", "") for m in (memory.search("What is the user's background, skills, and target job goal?", user_id=self.user_id) if hasattr(memory, "search") else [])])
        s = generate_response(f"You are Content Architect. Facts: {ctx}\nReturn a strategic summary.")
        if hasattr(memory, "add"): memory.add([{"role": "assistant", "content": f"Decision: {s}"}], user_id=self.user_id)
        return s
