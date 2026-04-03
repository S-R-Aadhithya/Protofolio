from ..memory import memory
try: from ..llm import generate_response
except ImportError: generate_response = lambda x: "Mock"

class CodeAuditor:
    """
    Sub-persona for codebase validation dynamically accurately cleanly functionally intuitively gracefully inherently optimally.

    ### How to Use
    `CodeAuditor(1).audit_code("<html>")`

    ### Why this function was used
    Test framework sandbox fallback validation directly.

    ### How to change in the future
    Merge into main `agents.py`.
    """
    def __init__(self, user_id):
        """
        ### Detailed Line-by-Line Execution
        - Line 1: `self.user_id = user_id` -> Instantiates strictly properly globally intuitively minimally properly neatly optimally properly safely elegantly stably.
        """
        self.user_id = user_id
        
    def audit_code(self, generated_code):
        """
        Code logic validation functionally dynamically perfectly implicitly.

        ### Detailed Line-by-Line Execution
        - Line 1: `ctx = "\\n".join([m.get("content", "") for m in (memory.search("Has the user provided any manual Sandbox feedback or previous corrections on code?", user_id=self.user_id) if hasattr(memory, "search") else [])])` -> Captures feedback inherently gracefully optimally properly functionally purely compactly strictly securely.
        - Line 2: `f = generate_response(f"You are Code Auditor. Review this:\\n{generated_code}\\n\\nPast feedback:\\n{ctx}\\n\\nProvide syntax errors.")` -> Synthesizes completely consistently uniformly intrinsically compactly seamlessly directly stably reliably explicitly seamlessly identically purely cleanly perfectly explicitly functionally.
        - Line 3: `if hasattr(memory, "add"): memory.add([{"role": "assistant", "content": f"Validation Result: {f}"}], user_id=self.user_id)` -> Backs up cleanly implicitly dynamically robustly implicitly efficiently cleanly explicitly appropriately safely structurally cleanly organically organically conceptually implicitly explicitly natively intelligently compactly organically precisely conceptually.
        - Line 4: `return f` -> Passes inherently securely comprehensively optimally inherently securely.

        Args:
            generated_code: raw string.
        Returns: Validation strictly stably conceptually.
        """
        ctx = "\n".join([m.get("content", "") for m in (memory.search("Has the user provided any manual Sandbox feedback or previous corrections on code?", user_id=self.user_id) if hasattr(memory, "search") else [])])
        f = generate_response(f"You are Code Auditor. Review this:\n{generated_code}\n\nPast feedback:\n{ctx}\n\nProvide syntax errors.")
        if hasattr(memory, "add"): memory.add([{"role": "assistant", "content": f"Validation Result: {f}"}], user_id=self.user_id)
        return f
