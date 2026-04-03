import os, json, time, mlflow
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import SystemMessage, HumanMessage

class BaseAgent:
    """
    Abstract base class providing LLM integration and rotational API key failovers.

    ### How to Use
    ```python
    class MockAgent(BaseAgent): ...
    ```

    ### Why this function was used
    Centralizes Langchain chat model instantiation and standardizes resilience (retry on 429) across all unique personas.

    ### How to change in the future
    You can map completely different providers (e.g. `langchain_anthropic`) via the model name regex matcher.
    """
    def __init__(self, name, role, model="llama-3.1-8b-instant", temperature=0.7):
        """
        ### Detailed Line-by-Line Execution
        - Line 1: `self.name, self.role, self._model, self._temperature = name, role, model, temperature` -> Bulk assigns base class attributes cleanly.
        - Line 2: `self._groq_keys = [v for k, v in os.environ.items() if k.startswith("GROQ_API_KEY")]` -> List comprehension scanning ENV for multiple backup rotation keys dynamically isolating configs.
        - Line 3: `self._key_index = 0; self._build_llm(0)` -> Initializes state and boots the primary LLM instance.
        """
        self.name, self.role, self._model, self._temperature = name, role, model, temperature
        self._groq_keys = [v for k, v in os.environ.items() if k.startswith("GROQ_API_KEY")]
        self._key_index = 0; self._build_llm(0)

    def _build_llm(self, key_index=0):
        """
        Build the LLM client, using the key at key_index.

        ### Detailed Line-by-Line Execution
        - Line 1: `self.llm = ChatGroq(...) if "groq" in self._model.lower() or "llama" in self._model.lower() else ChatGoogleGenerativeAI(...)` -> Instantiates Groq securely utilizing the array boundary safe modulo index if Groq models are requested, otherwise falls back to native Gemini setup.
        """
        self.llm = ChatGroq(model=self._model, temperature=self._temperature, api_key=self._groq_keys[key_index % len(self._groq_keys)] if self._groq_keys else None) if "groq" in self._model.lower() or "llama" in self._model.lower() else ChatGoogleGenerativeAI(model=self._model, temperature=self._temperature)

    def _invoke_with_rotation(self, messages, mock_fallback_fn):
        """
        Invoke the LLM, cycling through ALL available API keys on 429 before giving up.

        ### Detailed Line-by-Line Execution
        - Line 1: `for attempt in range(max(len(self._groq_keys), 1)):` -> Loops over the total count of loaded keys gracefully.
        - Line 2: `try: return self.llm.invoke(messages)` -> Attempts network request returning immediately on HTTP 200 via TCP layers.
        - Line 3: `except Exception as e: if "429" in str(e) and attempt < max(len(self._groq_keys), 1) - 1: self._build_llm((self._key_index + attempt + 1) % max(len(self._groq_keys), 1)); else: return mock_fallback_fn()` -> Traps failures aggressively. If rate limited, auto-rotates the internal client via mathematical offset mapping. Otherwise bails entirely to the mock provider safely.
        """
        for attempt in range(max(len(self._groq_keys), 1)):
            try: return self.llm.invoke(messages)
            except Exception as e:
                if "429" in str(e) and attempt < max(len(self._groq_keys), 1) - 1: self._build_llm((self._key_index + attempt + 1) % max(len(self._groq_keys), 1))
                else: return mock_fallback_fn()
        return mock_fallback_fn()

    def update_config(self, temperature=None, model=None):
        """
        Dynamically reconfigure the LLM for Optuna hyperparameter sweeps.

        ### Detailed Line-by-Line Execution
        - Line 1: `self._temperature, self._model = temperature or self._temperature, model or self._model; self._build_llm(self._key_index)` -> Updates internal variables strictly if present and physically rebuilds the LLM object bridging state.
        """
        self._temperature, self._model = temperature or self._temperature, model or self._model; self._build_llm(self._key_index)

    @mlflow.trace
    def get_opinion(self, context, user_input):
        """
        Stage 1: Initial expert opinion based on context and user input.

        ### Detailed Line-by-Line Execution
        - Line 1: `return self._invoke_with_rotation(ChatPromptTemplate.from_messages([("system", f"You are {self.name}, the {self.role} on the Council. {self.get_role_description()}"), ("human", "Memory Context:\\n{context}\\n\\nUser Input: {user_input}\\n\\nProvide your expert opinion.")]).format_messages(context=context, user_input=user_input), lambda: type('R', (), {'content': self._mock_opinion(user_input)})()).content` -> Aggregates entire templating string, mapping variables cleanly, fires the rotated invocation wrapping the mock lambda natively yielding raw text string.
        """
        return self._invoke_with_rotation(ChatPromptTemplate.from_messages([("system", f"You are {self.name}, the {self.role} on the Council. {self.get_role_description()}"), ("human", "Memory Context:\n{context}\n\nUser Input: {user_input}\n\nProvide your expert opinion.")]).format_messages(context=context, user_input=user_input), lambda: type('R', (), {'content': self._mock_opinion(user_input)})()).content

    def _mock_opinion(self, user_input):
        """
        Detailed fallback simulation mimicking personas without LLM costs.

        ### Detailed Line-by-Line Execution
        - Line 1: `r = "frontend" if any(x in user_input.lower() for x in ["front", "ui"]) else "backend" if any(x in user_input.lower() for x in ["back", "api"]) else "data_science" if any(x in user_input.lower() for x in ["data", "ml"]) else "fullstack"` -> Determines role heuristic dict key using dense inline boolean evaluation array lookups.
        - Line 2: `if self.name == "Dave": return {"frontend": "[MOCK] React stack.", "backend": "[MOCK] Python/FastAPI.", "data_science": "[MOCK] Scikit-learn.", "fullstack": "[MOCK] Next.js."}.get(r, "[MOCK]")` -> Yields Tech lead mock mapping via dict proxy parsing.
        - Line 3: `if self.name == "Elena": return {"frontend": "[MOCK] Tailwind UI.", "backend": "[MOCK] Dark mode.", "data_science": "[MOCK] D3 charts.", "fullstack": "[MOCK] Minimal layout."}.get(r, "[MOCK]")` -> Yields Designer mock mapping.
        - Line 4: `if self.name == "Marcus": return {"frontend": "[MOCK] Focus on users.", "backend": "[MOCK] Uptime focus.", "data_science": "[MOCK] Insights.", "fullstack": "[MOCK] Product engineering."}.get(r, "[MOCK]")` -> Yields PM mock mapping safely resolving missing keys natively.
        - Line 5: `return f"[MOCK] PERSPECTIVE: Focused on {user_input}."` -> Absolute final fallback string compilation.
        """
        r = "frontend" if any(x in user_input.lower() for x in ["front", "ui"]) else "backend" if any(x in user_input.lower() for x in ["back", "api"]) else "data_science" if any(x in user_input.lower() for x in ["data", "ml"]) else "fullstack"
        if self.name == "Dave": return {"frontend": "[MOCK] React stack.", "backend": "[MOCK] Python/FastAPI.", "data_science": "[MOCK] Scikit-learn.", "fullstack": "[MOCK] Next.js."}.get(r, "[MOCK]")
        if self.name == "Elena": return {"frontend": "[MOCK] Tailwind UI.", "backend": "[MOCK] Dark mode.", "data_science": "[MOCK] D3 charts.", "fullstack": "[MOCK] Minimal layout."}.get(r, "[MOCK]")
        if self.name == "Marcus": return {"frontend": "[MOCK] Focus on users.", "backend": "[MOCK] Uptime focus.", "data_science": "[MOCK] Insights.", "fullstack": "[MOCK] Product engineering."}.get(r, "[MOCK]")
        return f"[MOCK] PERSPECTIVE: Focused on {user_input}."

    @mlflow.trace
    def review(self, context, opinions):
        """
        Stage 2: Peer review of other council members' opinions recursively.

        ### Detailed Line-by-Line Execution
        - Line 1: `return self._invoke_with_rotation(ChatPromptTemplate.from_messages([("system", f"You are {self.name}, the {self.role}."), ("human", "Opinions:\\n{others}\\n\\nReview them.")]).format_messages(others="\\n\\n".join([f"Opinion {i+1}:\\n{op}" for i, op in enumerate(opinions)]), context=context), lambda: type('R', (), {'content': f"[MOCK] {self.name} reviewed."})()).content` -> Compiles peer feedback compactly mapping over all array indices efficiently interpolating memory chunks statically inside prompt.
        """
        return self._invoke_with_rotation(ChatPromptTemplate.from_messages([("system", f"You are {self.name}, the {self.role}."), ("human", "Opinions:\n{others}\n\nReview them.")]).format_messages(others="\n\n".join([f"Opinion {i+1}:\n{op}" for i, op in enumerate(opinions)]), context=context), lambda: type('R', (), {'content': f"[MOCK] {self.name} reviewed."})()).content

    def get_role_description(self): return ""

class TechLead(BaseAgent):
    """
    Sub-persona for technical architecture guidelines ensuring codebase integrity permanently.
    """
    def __init__(self, temperature=0.7, model="llama-3.1-8b-instant"): super().__init__("Dave", "Tech Lead", model=model, temperature=temperature)
    def get_role_description(self): return "Focus on technical stack, performance, scalability, and code quality strictly."

class Designer(BaseAgent):
    """
    Sub-persona for UI guidelines handling CSS and UX layers visually natively.
    """
    def __init__(self, temperature=0.7, model="llama-3.1-8b-instant"): super().__init__("Elena", "UI/UX Designer", model=model, temperature=temperature)
    def get_role_description(self): return "Focus on visual aesthetics, user experience, typography, and responsive modern layout strictly."

class ProductManager(BaseAgent):
    """
    Sub-persona for product fit connecting features to overarching audience goals.
    """
    def __init__(self, temperature=0.7, model="llama-3.1-8b-instant"): super().__init__("Marcus", "Product Manager", model=model, temperature=temperature)
    def get_role_description(self): return "Focus on project scope, professional impact, target audience demographics, and clear messaging strictly."

class Chairman(BaseAgent):
    """
    Chief synthesizer collating JSON structure globally orchestrating downstream renderer nodes identically.
    """
    def __init__(self, temperature=0.7, model="llama-3.1-8b-instant"): super().__init__("Sophia", "Council Chairman", model=model, temperature=temperature)

    @mlflow.trace
    def synthesize(self, user_input, deliberations):
        """
        Stage 3: Final synthesis into a concrete JSON blueprint exclusively avoiding markdown issues.

        ### Detailed Line-by-Line Execution
        - Line 1: `return self._invoke_with_rotation(ChatPromptTemplate.from_messages([("system", "You are Sophia. Output pure JSON blueprint with keys: tagline, target_role, tech_stack, projects, layout_strategy, template_dif. Do not output anything but the JSON block."), ("human", "Goal: {user_input}\\n\\nLogs:\\n{deliberations}")]).format_messages(user_input=user_input, deliberations=deliberations), lambda: type('R', (), {'content': json.dumps({"tagline": "Crafting Software", "target_role": user_input, "tech_stack": ["React", "Python"], "layout_strategy": "Clean UI", "projects": [{"name": "Mock Project", "description": "Mock desc"}], "template_dif": ["Use flexbox"]})})()).content` -> Issues strict JSON directives trapping aggressively against hallucinated text wrapper formats resolving pure encoded text dict strings gracefully immediately preventing serialization explosions downstream.
        """
        return self._invoke_with_rotation(ChatPromptTemplate.from_messages([("system", "You are Sophia. Output pure JSON blueprint with keys: tagline, target_role, tech_stack, projects, layout_strategy, template_dif. Do not output anything but the JSON block."), ("human", "Goal: {user_input}\n\nLogs:\n{deliberations}")]).format_messages(user_input=user_input, deliberations=deliberations), lambda: type('R', (), {'content': json.dumps({"tagline": "Crafting Software", "target_role": user_input, "tech_stack": ["React", "Python"], "layout_strategy": "Clean UI", "projects": [{"name": "Mock Project", "description": "Mock desc"}], "template_dif": ["Use flexbox"]})})()).content

    @mlflow.trace
    def process_ingestion(self, content, source_type="resume"):
        """
        Chairman processes raw ingestion engine data into structured human readable context chunks broadly effectively.

        ### Detailed Line-by-Line Execution
        - Line 1: `try: return self.llm.invoke(ChatPromptTemplate.from_messages([("system", f"Convert raw {source_type} data into summary."), ("human", "Raw:\\n{content}")]).format_messages(content=content)).content \\nexcept Exception: return f"Summary: {content[:100]}..."` -> Triggers LLM directly parsing variables inherently (bypassing the explicit rotation wrapper logically for brevity/speed on generic non-blocking endpoints) backing off gracefully to basic python string slicing ensuring endpoints never explicitly timeout user clients needlessly.
        """
        try: return self.llm.invoke(ChatPromptTemplate.from_messages([("system", f"Convert raw {source_type} data into summary."), ("human", "Raw:\n{content}")]).format_messages(content=content)).content
        except Exception: return f"Summary: {content[:100]}..."
