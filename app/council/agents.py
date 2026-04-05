import os
import json
import time
import mlflow
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import SystemMessage, HumanMessage

class BaseAgent:
    def __init__(self, name, role, model="llama-3.1-8b-instant", temperature=0.7):
        self.name = name
        self.role = role
        self._model = model
        self._temperature = temperature
        self._groq_keys = [v for k, v in os.environ.items() if k.startswith("GROQ_API_KEY")]
        self._key_index = 0
        self._build_llm(0)

    def _build_llm(self, key_index=0):
        """Build the LLM client, using the key at key_index."""
        if "groq" in self._model.lower() or "llama" in self._model.lower():
            api_key = self._groq_keys[key_index % len(self._groq_keys)] if self._groq_keys else None
            self.llm = ChatGroq(model=self._model, temperature=self._temperature, api_key=api_key)
        else:
            self.llm = ChatGoogleGenerativeAI(model=self._model, temperature=self._temperature)

    def _invoke_with_rotation(self, messages, mock_fallback_fn):
        """Invoke the LLM, cycling through ALL available API keys on 429 before giving up."""
        num_keys = max(len(self._groq_keys), 1)
        for attempt in range(num_keys):
            try:
                return self.llm.invoke(messages)
            except Exception as e:
                if "429" in str(e) and attempt < num_keys - 1:
                    next_index = (self._key_index + attempt + 1) % num_keys
                    print(f"WARNING: {self.name} got 429 on key [{attempt}], switching to key [{next_index}]...")
                    self._build_llm(key_index=next_index)
                else:
                    print(f"WARNING: {self.name} failed after trying {attempt+1} key(s): {e}")
                    return mock_fallback_fn()
        return mock_fallback_fn()

    def update_config(self, temperature=None, model=None):
        """Dynamically reconfigure the LLM for Optuna hyperparameter sweeps."""
        if temperature is not None:
            self._temperature = temperature
        if model is not None:
            self._model = model
        self._build_llm(self._key_index)

    @mlflow.trace
    def get_opinion(self, context, user_input):
        """Stage 1: Initial expert opinion based on context and user input."""
        system_msg = f"You are {self.name}, the {self.role} on the Council. {self.get_role_description()}"
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_msg),
            ("human", "Memory Context:\n{context}\n\nUser Input: {user_input}\n\nProvide your expert opinion for the portfolio plan. Be specific and reference details from the resume context.")
        ])
        messages = prompt.format_messages(context=context, user_input=user_input)
        result = self._invoke_with_rotation(messages, lambda: type('R', (), {'content': self._mock_opinion(user_input)})())
        return result.content

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
        others = "\n\n".join([f"Opinion {i+1}:\n{op}" for i, op in enumerate(opinions)])
        system_msg = f"You are {self.name}, the {self.role}. Review the following colleague opinions. Be critical and constructive."
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_msg),
            ("human", "Colleague Opinions:\n{others}\n\nMemory Context:\n{context}\n\nProvide your analysis and ranking.")
        ])
        messages = prompt.format_messages(others=others, context=context)
        
        def mock_review():
            if self.name == "Dave":   return type('R', (), {'content': "[MOCK] Tech Lead: Looks technically sound."})() 
            if self.name == "Elena":  return type('R', (), {'content': "[MOCK] Designer: Ensure accessibility standards."})() 
            if self.name == "Marcus": return type('R', (), {'content': "[MOCK] PM: Focus on user ROI."})() 
            return type('R', (), {'content': f"[MOCK] {self.name} reviewed."})() 
        
        result = self._invoke_with_rotation(messages, mock_review)
        return result.content

    def get_role_description(self):
        return ""

class TechLead(BaseAgent):
    def __init__(self, temperature=0.7, model="llama-3.1-8b-instant"):
        super().__init__("Dave", "Tech Lead", model=model, temperature=temperature)
    def get_role_description(self):
        return "Focus on technical stack, performance, scalability, and code quality."

class Designer(BaseAgent):
    def __init__(self, temperature=0.7, model="llama-3.1-8b-instant"):
        super().__init__("Elena", "UI/UX Designer", model=model, temperature=temperature)
    def get_role_description(self):
        return "Focus on visual aesthetics, user experience, typography, and responsive layout."

class ProductManager(BaseAgent):
    def __init__(self, temperature=0.7, model="llama-3.1-8b-instant"):
        super().__init__("Marcus", "Product Manager", model=model, temperature=temperature)
    def get_role_description(self):
        return "Focus on project scope, professional impact, target audience, and clear messaging."

class Chairman(BaseAgent):
    def __init__(self, temperature=0.7, model="llama-3.1-8b-instant"):
        super().__init__("Sophia", "Council Chairman", model=model, temperature=temperature)

    def _build_llm(self, key_index=0):
        """Try fine-tuned Ollama model first; fall back to base Groq/Gemini."""
        ollama_model = os.getenv("OLLAMA_MODEL")
        ollama_host  = os.getenv("OLLAMA_HOST", "http://localhost:11434")
        if ollama_model:
            try:
                from langchain_ollama import ChatOllama
                self.llm = ChatOllama(
                    model=ollama_model,
                    base_url=ollama_host,
                    temperature=self._temperature,
                    num_predict=1500,
                )
                self._using_ollama = True
                print(f"INFO: Chairman ✓ using fine-tuned Ollama model: {ollama_model}")
                return
            except Exception as e:
                print(f"WARNING: Ollama unavailable ({e}) — falling back to base model.")
        self._using_ollama = False
        super()._build_llm(key_index)

    # ── SME System Prompt — MUST MATCH finetune/generate_training_data.py ────
    _SME_SYSTEM_PROMPT = (
        "You are Sophia, the unified Council Chairman and Subject Matter Expert (SME).\n"
        "You simultaneously embody the perspectives of:\n"
        "  - Tech Lead   (technical stack, architecture, code quality)\n"
        "  - UI/UX Designer (visual aesthetics, layout, user experience)\n"
        "  - Product Manager (market positioning, impact framing, audience clarity)\n"
        "  - Council Approver (holistic assessment and final decision)\n\n"
        "Given a candidate's career goal and RAG-indexed professional data, produce a\n"
        "SINGLE valid JSON object. No markdown. No explanation. Only raw JSON.\n\n"
        "CRITICAL RULES:\n"
        "- Extract tech_stack ONLY from context. NEVER invent tools.\n"
        "- Extract work_experience ONLY from context. NEVER invent company names.\n"
        "- Extract projects ONLY from context. NEVER invent project names.\n"
        "- If a field cannot be populated from context, return [] for lists.\n\n"
        'Required JSON schema:\n'
        '{\n'
        '  \"tagline\": \"<specific 1-sentence headline for THIS person>\",\n'
        '  \"target_role\": \"<professional title>\",\n'
        '  \"tech_stack\": [\"<tool>\", \"...up to 10\"],\n'
        '  \"work_experience\": [{\"company\": \"...\", \"role\": \"...\", \"description\": \"1-2 sentences\"}],\n'
        '  \"projects\": [{\"name\": \"...\", \"description\": \"1-2 sentences\"}],\n'
        '  \"layout_strategy\": \"<2-3 sentence layout and design philosophy>\",\n'
        '  \"template_dif\": [\"<CSS/HTML tweak>\", \"...3-5 items\"],\n'
        '  \"approval_verdict\": {\n'
        '    \"approved\": true,\n'
        '    \"confidence_score\": 0.9,\n'
        '    \"council_decision\": \"APPROVED\",\n'
        '    \"tech_notes\": \"<tech lead 1-2 sentences>\",\n'
        '    \"design_notes\": \"<designer 1-2 sentences>\",\n'
        '    \"market_notes\": \"<PM 1-2 sentences>\",\n'
        '    \"key_strengths\": [\"<strength>\"],\n'
        '    \"gaps_to_address\": [\"<gap>\"]}\n'
        '}'
    )

    @mlflow.trace
    def synthesize(self, user_input, deliberations, context=""):
        """Stage 3: Final synthesis into a concrete JSON blueprint."""
        system_msg = """You are Sophia, the Council Chairman. Based on the deliberations below, produce a final portfolio blueprint as STRICT JSON.

You MUST output ONLY a raw JSON object (no markdown, no ```json blocks, no explanation). The JSON must contain ALL of these keys:
- "tagline": A specific, compelling 1-sentence headline for this exact person (NOT generic).
- "target_role": Their professional title.
- "tech_stack": A list of up to 10 specific tools. Do not invent a tech stack. Only list tools explicitly mentioned in the context. If none are found, return ["HTML", "CSS", "JavaScript"].
- "work_experience": Extracted directly from the provided user memory/resume. A list of up to 4 objects, each with "company", "role", and "description" (1-2 sentences). ABSOLUTELY CRITICAL: If the provided Memory Context does not explicitly list real company names for work experience, YOU MUST RETURN AN EMPTY LIST []. NEVER invent names like 'ABC Corporation', 'GHI Inc.', or 'DEF Startups'.
- "projects": A list of up to 3 objects. Extracted directly from the provided memory. If the provided Memory Context does not list real projects, YOU MUST RETURN AN EMPTY LIST []. NEVER invent fake project names or dummy companies.
- "layout_strategy": A 2-3 sentence description of the page layout and design philosophy for this person's portfolio.
- "template_dif": A list of 3-5 specific CSS/HTML tweaks (e.g. "Use purple accent color #7c3aed").

Do NOT use placeholder names. Use real, domain-specific project and company names based purely on the memory context. If they are missing, omit them."""
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_msg),
            ("human", "User Goal: {user_input}\n\nMemory Context (Use this for tech_stack and work_experience):\n{context}\n\nDeliberations:\n{deliberations}\n\nOutput ONLY the JSON object.")
        ])
        messages = prompt.format_messages(user_input=user_input, deliberations=deliberations, context=context)

        def mock_synthesis():
            import random
            goal = user_input.lower()
            if "ui" in goal or "ux" in goal or "figma" in goal or "design" in goal:
                tagline = "Crafting Intuitive Experiences Through Human-Centered Design"
                stack = ["Figma", "Adobe XD", "Sketch", "HTML5", "CSS3", "Tailwind CSS", "React.js", "Zeplin"]
            elif "front" in goal:
                tagline = "Mastering the UI/UX Frontier"
                stack = ["React", "TypeScript", "Tailwind CSS", "Vite", "Framer Motion"]
            elif "back" in goal:
                tagline = "Architecting Robust Backends"
                stack = ["Python", "FastAPI", "PostgreSQL", "Redis", "Docker", "AWS"]
            else:
                tagline = "Full-Stack Solution Architecture"
                stack = ["Next.js", "TypeScript", "PostgreSQL", "Prisma", "Node.js"]
            mock_blueprint = {
                "tagline": tagline,
                "target_role": user_input,
                "tech_stack": stack,
                "layout_strategy": "A clean, portfolio-first layout with hero, featured projects grid, and skills section.",
                "work_experience": [],
                "projects": [
                    {"name": "E-Commerce Redesign", "description": "Led a full UI overhaul increasing user retention by 35%. Built with Figma components and a design system."},
                    {"name": "Mobile App UX", "description": "Designed end-to-end user flows for a healthcare mobile app. Conducted usability testing with 50+ participants."},
                    {"name": "Design System", "description": "Established a scalable component library used across 5 product lines. Improved design-to-dev handoff speed by 40%."}
                ],
                "template_dif": ["Use purple accent color #7c3aed", "Use Inter font family", "Add subtle box-shadow to project cards"]
            }
            return type('R', (), {'content': json.dumps(mock_blueprint)})()

        result = self._invoke_with_rotation(messages, mock_synthesis)
        return result.content

    @mlflow.trace
    def sme_synthesize(self, user_input: str, rag_context: str) -> str:
        """
        RAG-mode: single LLM call replacing the 7-call deliberation pipeline.
        Returns raw JSON string containing blueprint + approval_verdict.
        """
        prompt = ChatPromptTemplate.from_messages([
            ("system", self._SME_SYSTEM_PROMPT),
            ("human",  "Career Goal: {user_input}\n\nRAG Context:\n{context}\n\nOutput ONLY the JSON object."),
        ])
        messages = prompt.format_messages(user_input=user_input, context=rag_context)
        result = self._invoke_with_rotation(
            messages,
            lambda: type('R', (), {'content': self._mock_sme_synthesis(user_input)})()
        )
        return result.content

    def _mock_sme_synthesis(self, user_input: str) -> str:
        """Deterministic mock for CI / no-API environments."""
        goal = user_input.lower()
        if any(k in goal for k in ["ml", "machine", "ai", "data science"]):
            stack = ["Python", "PyTorch", "Scikit-Learn", "MLflow", "Hugging Face", "Docker"]
            tagline = "Building Intelligent Systems at the Intersection of Data and Engineering"
        elif any(k in goal for k in ["front", "ui", "ux", "design"]):
            stack = ["React", "TypeScript", "Next.js", "Tailwind CSS", "Framer Motion"]
            tagline = "Crafting Pixel-Perfect Interfaces with Purposeful Interaction Design"
        elif any(k in goal for k in ["back", "api", "server"]):
            stack = ["Python", "FastAPI", "PostgreSQL", "Redis", "Docker", "AWS"]
            tagline = "Architecting Reliable Backends That Scale with Confidence"
        elif any(k in goal for k in ["devops", "sre", "cloud"]):
            stack = ["Kubernetes", "Terraform", "Docker", "Prometheus", "AWS", "GitHub Actions"]
            tagline = "Engineering the Infrastructure That Powers Modern Software at Scale"
        else:
            stack = ["Next.js", "TypeScript", "PostgreSQL", "Node.js", "Docker"]
            tagline = "Full-Stack Engineer Delivering End-to-End Product Excellence"
        blueprint = {
            "tagline": tagline, "target_role": user_input, "tech_stack": stack,
            "work_experience": [], "projects": [],
            "layout_strategy": "Clean single-page portfolio with hero, skills grid, and project cards. Mobile-first responsive layout.",
            "template_dif": ["Gradient accent #6d28d9 → #3b82f6", "Inter font family", "Subtle card shadows", "Thin gradient dividers"],
            "approval_verdict": {
                "approved": True, "confidence_score": 0.82,
                "council_decision": "APPROVED",
                "tech_notes": "[MOCK] Technical stack aligns well with target role requirements.",
                "design_notes": "[MOCK] Recommend dark theme with gradient accents for a modern feel.",
                "market_notes": "[MOCK] Target role positioning is competitive in the current market.",
                "key_strengths": ["Technical foundation", "Consistent project portfolio"],
                "gaps_to_address": ["Add quantifiable metrics", "Include open-source contributions"],
            },
        }
        return json.dumps(blueprint)

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
