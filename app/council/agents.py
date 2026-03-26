import os
import json
import mlflow
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import SystemMessage, HumanMessage

class BaseAgent:
    def __init__(self, name, role, model="gemini-1.5-flash"):
        self.llm = ChatGoogleGenerativeAI(model=model, temperature=0.7)
        self.name = name
        self.role = role

    @mlflow.trace
    def get_opinion(self, context, user_input):
        """Stage 1: Initial expert opinion based on context and user input."""
        api_key = os.getenv('GEMINI_API_KEY', '')
        if not api_key or 'your_gemini_api_key' in api_key:
            return self._mock_opinion(user_input)

        system_msg = f"You are {self.name}, the {self.role} on the Council. {self.get_role_description()}"
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_msg),
            ("human", f"Memory Context:\n{context}\n\nUser Input: {user_input}\n\nProvide your expert opinion for the portfolio plan.")
        ])
        response = self.llm.invoke(prompt.format_messages())
        return response.content

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
        api_key = os.getenv('GEMINI_API_KEY', '')
        if not api_key or 'your_gemini_api_key' in api_key:
            # Enhanced mock critiques
            if self.name == "Dave":
                return f"[MOCK] Tech Lead's Critique: Elena's design looks great, but let's ensure the glassmorphism doesn't impact Lighthouse scores. Marcus, let's make sure the 'business value' we claim is technically verifiable in the code."
            if self.name == "Elena":
                return f"[MOCK] Designer's Critique: Dave's stack is solid, but we need to ensure the mobile UX isn't an afterthought. Marcus, I'll need more 'user stories' to inform the navigation flow."
            if self.name == "Marcus":
                return f"[MOCK] PM's Critique: Dave, don't get too bogged down in the backend scalability if the user can't see the value. Elena, let's keep the design professional; too many animations might distract a busy recruiter."
            return f"[MOCK] {self.name} has reviewed the opinions and provides constructive feedback."

        others = "\n\n".join([f"Opinion {i+1}:\n{op}" for i, op in enumerate(opinions)])
        system_msg = f"You are {self.name}, the {self.role}. Review the following colleague opinions. Be critical and constructive."
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_msg),
            ("human", f"Colleague Opinions:\n{others}\n\nMemory Context:\n{context}\n\nProvide your analysis and ranking.")
        ])
        response = self.llm.invoke(prompt.format_messages())
        return response.content

    def get_role_description(self):
        return ""

class TechLead(BaseAgent):
    def __init__(self):
        super().__init__("Dave", "Tech Lead")
    def get_role_description(self):
        return "Focus on technical stack, performance, scalability, and code quality."

class Designer(BaseAgent):
    def __init__(self):
        super().__init__("Elena", "UI/UX Designer")
    def get_role_description(self):
        return "Focus on visual aesthetics, user experience, typography, and responsive layout."

class ProductManager(BaseAgent):
    def __init__(self):
        super().__init__("Marcus", "Product Manager")
    def get_role_description(self):
        return "Focus on project scope, professional impact, target audience, and clear messaging."

class Chairman(BaseAgent):
    def __init__(self):
        super().__init__("Sophia", "Council Chairman", model="gemini-1.5-flash")

    @mlflow.trace
    def synthesize(self, user_input, deliberations):
        """Stage 3: Final synthesis into a concrete JSON blueprint."""
        api_key = os.getenv('GEMINI_API_KEY', '')
        if not api_key or 'your_gemini_api_key' in api_key:
            import json
            goal = user_input.lower()
            
            # Dynamic Tech Stack Selection
            if "front" in goal:
                tagline = f"Mastering the UI/UX Frontier"
                stack = ["React", "TypeScript", "Tailwind CSS", "Vite", "Framer Motion"]
            elif "back" in goal:
                tagline = f"Architecting Robust Backends"
                stack = ["Python", "FastAPI", "PostgreSQL", "Redis", "Docker", "AWS"]
            elif "data" in goal or "ai" in goal:
                tagline = f"Turning Data into Decisions"
                stack = ["Python", "PyTorch", "Pandas", "Scikit-Learn", "SQL", "Tableau"]
            else:
                tagline = f"Full-Stack Solution Architecture"
                stack = ["Next.js", "TypeScript", "PostgreSQL", "Prisma", "Node.js"]

            mock_blueprint = {
                "tagline": tagline,
                "tech_stack": stack,
                "layout_strategy": "A results-oriented layout with deep-dives into your most complex work.",
                "projects": [
                    {"name": "Representative Work A", "description": "High-impact project showcasing core skills and expertise."},
                    {"name": "Representative Work B", "description": "Complex implementation focused on solving real-world challenges."}
                ]
            }
            return json.dumps(mock_blueprint)

        system_msg = "You are Sophia, the Council Chairman. You take expert deliberations and produce a final portfolio blueprint in JSON format."
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_msg),
            ("human", f"User Goal: {user_input}\n\nDeliberations:\n{deliberations}\n\nOutput a JSON blueprint with keys: 'projects', 'tech_stack', 'layout_strategy', 'tagline'.")
        ])
        response = self.llm.invoke(prompt.format_messages())
        return response.content
