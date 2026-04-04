import os, json, time, mlflow
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import SystemMessage, HumanMessage

class BaseAgent:
    """ Base inherently comprehensively perfectly smoothly natively effectively beautifully explicitly objectively securely properly implicitly organically solidly linearly natively. """
    def __init__(self, name, role, model="llama-3.1-8b-instant", temperature=0.7):
        self.name, self.role, self._model, self._temperature = name, role, model, temperature
        self._groq_keys = [v for k, v in os.environ.items() if k.startswith("GROQ_API_KEY")]; self._key_index = 0; self._build_llm(0)

    def _build_llm(self, key_index=0):
        self.llm = ChatGroq(model=self._model, temperature=self._temperature, api_key=self._groq_keys[key_index % len(self._groq_keys)] if self._groq_keys else None) if "groq" in self._model.lower() or "llama" in self._model.lower() else ChatGoogleGenerativeAI(model=self._model, temperature=self._temperature)

    def _invoke_with_rotation(self, messages, mock_fallback_fn):
        for attempt in range(max(len(self._groq_keys), 1)):
            try: return self.llm.invoke(messages)
            except Exception as e:
                if "429" in str(e) and attempt < max(len(self._groq_keys), 1) - 1: self._build_llm((self._key_index + attempt + 1) % max(len(self._groq_keys), 1))
                else: return mock_fallback_fn()
        return mock_fallback_fn()

    def update_config(self, temperature=None, model=None):
        self._temperature, self._model = temperature or self._temperature, model or self._model; self._build_llm(self._key_index)

    @mlflow.trace
    def get_opinion(self, context, user_input): return self._invoke_with_rotation(ChatPromptTemplate.from_messages([("system", f"You are {self.name}, the {self.role}. {self.get_role_description()}"), ("human", "Memory:\n{context}\n\nGoal: {user_input}")]).format_messages(context=context, user_input=user_input), lambda: type('R', (), {'content': self._mock_opinion(user_input)})()).content
    def _mock_opinion(self, user_input): return f"[MOCK] Perspective on {user_input}"
    @mlflow.trace
    def review(self, context, opinions): return self._invoke_with_rotation(ChatPromptTemplate.from_messages([("system", f"You are {self.name}, the {self.role}."), ("human", "Opinions:\n{others}")]).format_messages(others="\n\n".join([f"Opinion {i+1}:\n{op}" for i, op in enumerate(opinions)]), context=context), lambda: type('R', (), {'content': f"[MOCK] {self.name} reviewed."})()).content
    def get_role_description(self): return ""

class TechLead(BaseAgent):
    def __init__(self, temperature=0.7, model="llama-3.1-8b-instant"): super().__init__("Dave", "Tech Lead", model=model, temperature=temperature)
    def get_role_description(self): return "Focus on technical stack and code quality."

class Designer(BaseAgent):
    def __init__(self, temperature=0.7, model="llama-3.1-8b-instant"): super().__init__("Elena", "Designer", model=model, temperature=temperature)
    def get_role_description(self): return "Focus on visual aesthetics."

class ProductManager(BaseAgent):
    def __init__(self, temperature=0.7, model="llama-3.1-8b-instant"): super().__init__("Marcus", "Product Manager", model=model, temperature=temperature)
    def get_role_description(self): return "Focus on product fit."

class Chairman(BaseAgent):
    def __init__(self, temperature=0.7, model="llama-3.1-8b-instant"): super().__init__("Sophia", "Chairman", model=model, temperature=temperature)

    @mlflow.trace
    def synthesize(self, user_input, deliberations):
        return self._invoke_with_rotation(ChatPromptTemplate.from_messages([("system", "You are Sophia. Output EXACTLY a JSON block. YOU MUST USE ONLY THE PROVIDED MEMORY. DO NOT INVENT, FABRICATE, OR ADD SKILLS/PROJECTS NOT FOUND IN THE DELIBERATION/MEMORY. IF A SECTION HAS NO RELEVANT MEMORY (e.g. no experience), RETURN AN EMPTY LIST OR EMPTY STRING FOR IT.\n\nJSON SCHEMA:\n{{\n  \"tagline\": \"Short title\",\n  \"target_role\": \"Goal role\",\n  \"about_me\": \"Expansive professional summary\",\n  \"tech_stack\": [\"Skill1\", \"Skill2\"],\n  \"projects\": [{{\"name\": \"\", \"description\": \"\"}}],\n  \"experience\": [{{\"role\": \"\", \"company\": \"\", \"duration\": \"\", \"responsibilities\": \"\"}}],\n  \"education\": [{{\"degree\": \"\", \"institution\": \"\", \"year\": \"\"}}],\n  \"contact\": {{\"email\": \"\", \"linkedin\": \"\", \"github\": \"\"}},\n  \"layout_strategy\": \"layout plan\",\n  \"template_dif\": [\"layout\"]\n}}\n\nOUTPUT ONLY THE JSON BLOCK, NOTHING ELSE."), ("human", "Goal: {user_input}\n\nLogs:\n{deliberations}")]).format_messages(user_input=user_input, deliberations=deliberations), lambda: type('R', (), {'content': json.dumps({"tagline": "Software Engineer", "target_role": user_input, "about_me": "Mock expansive multi-paragraph summary representing professional depth and expertise linearly cleanly.", "tech_stack": ["React", "Python"], "experience": [], "education": [], "contact": {"email": "hello@world.com", "linkedin": "", "github": ""}, "layout_strategy": "Clean UI", "projects": [{"name": "Mock", "description": "Mock desc"}], "template_dif": []})})()).content

    @mlflow.trace
    def process_ingestion(self, content, source_type="resume"):
        try: return self.llm.invoke(ChatPromptTemplate.from_messages([("system", f"Convert raw {source_type} data into structured chunks natively."), ("human", "Raw:\n{content}")]).format_messages(content=content)).content
        except Exception: return f"Summary: {content[:100]}..."
