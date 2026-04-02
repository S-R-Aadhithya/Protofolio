import os
import json
import mlflow
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import SystemMessage, HumanMessage

class BaseAgent:
    def __init__(self, name, role, model="llama-3.1-70b-versatile", temperature=0.7):
        self.name = name
        self.role = role
        self._model = model
        self._temperature = temperature
        if "groq" in model.lower() or "llama" in model.lower():
            self.llm = ChatGroq(model=model, temperature=temperature)
        else:
            self.llm = ChatGoogleGenerativeAI(model=model, temperature=temperature)

    def update_config(self, temperature=None, model=None):
        """Dynamically reconfigure the LLM for Optuna hyperparameter sweeps."""
        if temperature is not None:
            self._temperature = temperature
        if model is not None:
            self._model = model
        
        if "groq" in self._model.lower() or "llama" in self._model.lower():
            self.llm = ChatGroq(model=self._model, temperature=self._temperature)
        else:
            self.llm = ChatGoogleGenerativeAI(model=self._model, temperature=self._temperature)

    @mlflow.trace
    def get_opinion(self, context, user_input):
        """Stage 1: Initial expert opinion based on context and user input."""
        try:
            system_msg = f"You are {self.name}, the {self.role} on the Council. {self.get_role_description()}"
            prompt = ChatPromptTemplate.from_messages([
                ("system", system_msg),
                ("human", "Memory Context:\n{context}\n\nUser Input: {user_input}\n\nProvide your expert opinion for the portfolio plan.")
            ])
            response = self.llm.invoke(prompt.format_messages(context=context, user_input=user_input))
            return response.content
        except Exception as e:
            print(f"WARNING: Agent {self.name} invocation failed: {e}. Falling back to mock.")
            return self._mock_opinion(user_input)

    def _mock_opinion(self, user_input):
        goal = user_input.lower()
        if "front" in goal or "ui" in goal:
            role_type = "frontend"
        elif "back" in goal or "api" in goal or "server" in goal:
            role_type = "backend"
        elif "data" in goal or "machine" in goal or "ai" in goal:
            role_type = "data_science"
        else:
            role_type = "fullstack"

        if self.name == "Dave": # Tech Lead
            recommendations = {
                "frontend": "I recommend a React/Next.js stack with TypeScript to ensure type safety and optimal performance. We'll focus on component-driven architecture.",
                "backend": "We should go with a robust Python/FastAPI or Node.js backend, focusing on database migrations, scalability, and secure JWT authentication.",
                "data_science": "A Python-centric stack using Pandas, Scikit-learn, and potentially TensorFlow is key. We must highlight your data pipeline and model accuracy metrics.",
                "fullstack": "A modern Full Stack approach like the T3 stack or Next.js with Prisma and PostgreSQL will show you can handle both ends efficiently."
            }
            return f"[MOCK] As Tech Lead, I've reviewed your goal. {recommendations.get(role_type)}"

        if self.name == "Elena": # Designer
            recommendations = {
                "frontend": "This portfolio needs a pixel-perfect, highly responsive UI. I suggest using Tailwind CSS with subtle micro-animations and a sleek glassmorphism theme.",
                "backend": "While this is backend-focused, a clean 'developer-first' dashboard aesthetic with clear documentation layouts will stand out.",
                "data_science": "Focus on data visualization. We need interactive charts (possibly using D3.js or Recharts) to make your complex findings easy to digest.",
                "fullstack": "Balance is key. A consistent design language across the frontend while highlighting the complexity of the integrated features."
            }
            return f"[MOCK] Elena here. {recommendations.get(role_type)}"

        if self.name == "Marcus": # PM
            recommendations = {
                "frontend": "Market yourself as a specialist in user engagement. We'll frame your projects around 'time-to-interactive' and user-centric problem solving.",
                "backend": "Productivity and uptime are your selling points. We'll highlight how your systems solve scale issues and handle thousands of concurrent requests.",
                "data_science": "Lead with the insights. Your projects shouldn't just be 'models'; they are 'decision support tools' that drove 20% efficiency gains.",
                "fullstack": "Versatility is the product. We'll frame you as the 'Product-Minded Engineer' who can take a feature from concept to deployment independently."
            }
            return f"[MOCK] Marcus here. {recommendations.get(role_type)}"

        return f"[MOCK] PERSPECTIVE: Focused on {user_input}."

    @mlflow.trace
    def review(self, context, opinions):
        """Stage 2: Peer review of other council members' opinions."""
        try:
            others = "\n\n".join([f"Opinion {i+1}:\n{op}" for i, op in enumerate(opinions)])
            system_msg = f"You are {self.name}, the {self.role}. Review the following colleague opinions. Be critical and constructive."
            prompt = ChatPromptTemplate.from_messages([
                ("system", system_msg),
                ("human", "Colleague Opinions:\n{others}\n\nMemory Context:\n{context}\n\nProvide your analysis and ranking.")
            ])
            response = self.llm.invoke(prompt.format_messages(others=others, context=context))
            return response.content
        except Exception as e:
            print(f"WARNING: Agent {self.name} review failed: {e}. Falling back to mock critique.")
            if self.name == "Dave":
                return f"[MOCK] Tech Lead's Critique: Content looks technically sound, but let's optimize performance further."
            if self.name == "Elena":
                return f"[MOCK] Designer's Critique: The layout is clean, but ensure accessibility standards are met."
            if self.name == "Marcus":
                return f"[MOCK] PM's Critique: Focus on the user's return on investment (ROI) for these features."
            return f"[MOCK] {self.name} has reviewed the opinions."

    def get_role_description(self):
        return ""

class TechLead(BaseAgent):
    def __init__(self, temperature=0.7, model="llama-3.1-70b-versatile"):
        super().__init__("Dave", "Tech Lead", model=model, temperature=temperature)
    def get_role_description(self):
        return "Focus on technical stack, performance, scalability, and code quality."

class Designer(BaseAgent):
    def __init__(self, temperature=0.7, model="llama-3.1-70b-versatile"):
        super().__init__("Elena", "UI/UX Designer", model=model, temperature=temperature)
    def get_role_description(self):
        return "Focus on visual aesthetics, user experience, typography, and responsive layout."

class ProductManager(BaseAgent):
    def __init__(self, temperature=0.7, model="llama-3.1-70b-versatile"):
        super().__init__("Marcus", "Product Manager", model=model, temperature=temperature)
    def get_role_description(self):
        return "Focus on project scope, professional impact, target audience, and clear messaging."

class Chairman(BaseAgent):
    def __init__(self, temperature=0.7, model="llama-3.1-70b-versatile"):
        super().__init__("Sophia", "Council Chairman", model=model, temperature=temperature)

    @mlflow.trace
    def synthesize(self, user_input, deliberations):
        """Stage 3: Final synthesis into a concrete JSON blueprint with diff-like granularity."""
        try:
            system_msg = """You are Sophia, the Council Chairman. You take expert deliberations and produce a final portfolio blueprint.
            IMPORTANT: Output a JSON blueprint that includes not just final values, but also 'modifications' for the developer to apply to a base template.
            The JSON should have:
            - 'tagline': A catchy primary headline.
            - 'target_role': The professional title.
            - 'tech_stack': List of technologies.
            - 'projects': List of objects with 'name' and 'description'.
            - 'layout_strategy': A description of the visual flow.
            - 'template_dif': A list of specific HTML/CSS modifications in string format (e.g. "Add a neon border to project cards", "Use a monospaced font for the tagline").
            """
            prompt = ChatPromptTemplate.from_messages([
                ("system", system_msg),
                ("human", "User Goal: {user_input}\n\nDeliberations:\n{deliberations}\n\nOutput the JSON blueprint.")
            ])
            response = self.llm.invoke(prompt.format_messages(user_input=user_input, deliberations=deliberations))
            return response.content
        except Exception as e:
            print(f"WARNING: Chairman synthesis failed: {e}. Falling back to mock JSON.")
            import json
            import random
            goal = user_input.lower()

            if "front" in goal:
                tagline, stack = "Mastering the UI/UX Frontier", ["React", "TypeScript", "Tailwind CSS", "Vite", "Framer Motion"]
            elif "back" in goal:
                tagline, stack = "Architecting Robust Backends", ["Python", "FastAPI", "PostgreSQL", "Redis", "Docker", "AWS"]
            elif "data" in goal or "ai" in goal:
                tagline, stack = "Turning Data into Decisions", ["Python", "PyTorch", "Pandas", "Scikit-Learn", "SQL", "Tableau"]
            else:
                tagline, stack = "Full-Stack Solution Architecture", ["Next.js", "TypeScript", "PostgreSQL", "Prisma", "Node.js"]

            num_projects = random.randint(1, 4)
            projects = [{"name": f"Project {chr(65+i)} for {user_input[:10]}...", "description": f"Complexity level {random.randint(1, 10)} implementation."} for i in range(num_projects)]

            mock_blueprint = {
                "tagline": tagline if random.random() > 0.1 else "",
                "target_role": user_input,
                "tech_stack": stack,
                "layout_strategy": "A results-oriented layout.",
                "projects": projects,
                "template_dif": ["Use a clean sans-serif font", "Add subtle hover transitions"]
            }
            return json.dumps(mock_blueprint)

    @mlflow.trace
    def process_ingestion(self, content, source_type="resume"):
        """Chairman processes raw ingestion engine data into structured context."""
        try:
            system_msg = f"You are Sophia, the Chairman. Convert the following raw {source_type} data into a concise professional summary for the Council's use."
            prompt = ChatPromptTemplate.from_messages([
                ("system", system_msg),
                ("human", "Raw Content:\n{content}")
            ])
            response = self.llm.invoke(prompt.format_messages(content=content))
            return response.content
        except Exception as e:
            print(f"WARNING: process_ingestion failed: {e}")
            return f"Summary of {source_type} data: {content[:200]}..."
