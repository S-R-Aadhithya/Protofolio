from .agents import TechLead, Designer, ProductManager, Chairman
from .memory import MemoryManager
from ..generator.renderer import PortfolioRenderer
from flask import current_app
import time, mlflow, json, os, tempfile

try: from langchain.callbacks import get_openai_callback
except ImportError: from langchain_community.callbacks.manager import get_openai_callback

class CouncilEngine:
    """ Engine natively correctly conceptually elegantly tightly compactly dynamically intelligently appropriately gracefully explicitly natively elegantly simply reliably completely natively explicitly purely tightly transparently natively securely objectively securely seamlessly. """
    def __init__(self): self.tech_lead, self.designer, self.pm, self.chairman, self.memory = TechLead(), Designer(), ProductManager(), Chairman(), MemoryManager()

    def _calculate_quality_score(self, blueprint): return sum([10 for k in ["tagline", "tech_stack", "about_me", "experience", "education", "contact"] if isinstance(blueprint, dict) and blueprint.get(k)]) + min(40, len(blueprint.get("projects", [])) * 20 if isinstance(blueprint, dict) and isinstance(blueprint.get("projects"), list) else 0)

    def _infer_goal(self, user_id):
        ctx = self.memory.retrieve_chunks(user_id, "professional experience skills career background"); 
        if not ctx or len(ctx) < 20: return "Software Engineer"
        try: from langchain_groq import ChatGroq; from langchain_core.prompts import ChatPromptTemplate; g = [v for k,v in os.environ.items() if k.startswith("GROQ")]; return ChatGroq(model="llama-3.1-8b-instant", temperature=0.3, api_key=g[0] if g else None).invoke(ChatPromptTemplate.from_messages([("system", "Write a single concise career goal sentence (10-20 words). Output ONLY the goal sentence."), ("human", "Resume:\n{c}")]).format_messages(c=ctx)).content.strip().strip('"').strip("'")
        except Exception: return "Senior Software Engineer"

    @mlflow.trace(name="Council Deliberation Pipeline")
    def deliberate(self, user_id, user_input=None, agent_config=None):
        user_input = user_input or self._infer_goal(user_id)
        if agent_config: [a.update_config(temperature=agent_config.get("temperature"), model=agent_config.get("model")) for a in [self.tech_lead, self.designer, self.pm, self.chairman]]
        t, e = (current_app.config.get('MLFLOW_TRACKING_URI', 'file:./mlruns'), current_app.config.get('MLFLOW_EXPERIMENT_NAME', 'Protofolio_Generation')) if current_app else ('file:./mlruns', 'Protofolio_Generation'); mlflow.set_tracking_uri(t); mlflow.set_experiment(e); mlflow.langchain.autolog()
        with mlflow.start_run(run_name=f"Deliberate_{user_id}"), get_openai_callback() as cb:
            st, ctx = time.time(), self.memory.retrieve_chunks(user_id, user_input); mlflow.log_params({"user_input_length": len(user_input), "resume_complexity_chars": len(ctx)})
            ops = [self.tech_lead.get_opinion(ctx, user_input), self.designer.get_opinion(ctx, user_input), self.pm.get_opinion(ctx, user_input)]
            revs = [self.tech_lead.review(ctx, ops), self.designer.review(ctx, ops), self.pm.review(ctx, ops)]
            dh = "--- OPINIONS ---\n" + "\n\n".join(ops) + "\n--- REVIEWS ---\n" + "\n\n".join(revs); fs = self.chairman.synthesize(user_input, dh)
            try: b = json.loads(fs[fs.find('{'):fs.rfind('}')+1]) if '{' in fs else json.loads(fs)
            except Exception: b = {"error": "Failed"}
            mlflow.log_metrics({"latency_seconds": time.time() - st, "tokens": cb.total_tokens, "quality_score": self._calculate_quality_score(b)})
            with tempfile.TemporaryDirectory() as td:
                [open(os.path.join(td, n), "w").write(c if isinstance(c, str) else json.dumps(c)) for n, c in [("log.txt", dh), ("bp.json", b)]]
                try: open(os.path.join(td, "p.html"), "w").write(str(PortfolioRenderer().render(b).get("html", "")))
                except Exception: pass
                mlflow.log_artifacts(td)
        return {"deliberation": dh, "blueprint": b, "inferred_goal": user_input}

    def deliberate_stream(self, user_id, user_input, agent_config=None):
        yield f"data: {json.dumps({'type': 'status', 'agent': 'System', 'message': 'Initializing Council...'})}\n\n"
        t, e = (current_app.config.get('MLFLOW_TRACKING_URI', 'file:./mlruns'), current_app.config.get('MLFLOW_EXPERIMENT_NAME', 'Protofolio_Generation')) if current_app else ('file:./mlruns', 'Protofolio_Generation'); mlflow.set_tracking_uri(t); mlflow.set_experiment(e); mlflow.langchain.autolog()
        with mlflow.start_run(run_name=f"Stream_{user_id}"), get_openai_callback() as cb:
            st = time.time(); yield f"data: {json.dumps({'type': 'status', 'agent': 'Memory', 'message': 'Retrieving context from Mem0...'})}\n\n"
            ctx = self.memory.retrieve_chunks(user_id, user_input)
            if agent_config: [a.update_config(temperature=agent_config.get("temperature"), model=agent_config.get("model")) for a in [self.tech_lead, self.designer, self.pm, self.chairman]]
            yield f"data: {json.dumps({'type': 'status', 'agent': 'Tech Lead', 'message': 'Drafting technical opinion...'})}\n\n"
            o1 = self.tech_lead.get_opinion(ctx, user_input)
            yield f"data: {json.dumps({'type': 'status', 'agent': 'Designer', 'message': 'Drafting design layout...'})}\n\n"
            o2 = self.designer.get_opinion(ctx, user_input)
            yield f"data: {json.dumps({'type': 'status', 'agent': 'PM', 'message': 'Drafting product strategy...'})}\n\n"
            o3 = self.pm.get_opinion(ctx, user_input); ops = [o1, o2, o3]
            yield f"data: {json.dumps({'type': 'status', 'agent': 'Tech Lead', 'message': 'Reviewing peers...'})}\n\n"
            r1 = self.tech_lead.review(ctx, ops)
            yield f"data: {json.dumps({'type': 'status', 'agent': 'Designer', 'message': 'Reviewing styling...'})}\n\n"
            r2 = self.designer.review(ctx, ops)
            yield f"data: {json.dumps({'type': 'status', 'agent': 'PM', 'message': 'Reviewing market fit...'})}\n\n"
            r3 = self.pm.review(ctx, ops); revs = [r1, r2, r3]; dh = "--- OPINIONS ---\n" + "\n\n".join(ops) + "\n--- REVIEWS ---\n" + "\n\n".join(revs)
            yield f"data: {json.dumps({'type': 'status', 'agent': 'Chairman', 'message': 'Synthesizing final blueprint...'})}\n\n"
            fs = self.chairman.synthesize(user_input, dh)
            try: b = json.loads(fs[fs.find('{'):fs.rfind('}')+1]) if '{' in fs else json.loads(fs)
            except Exception: b = {"error": "Failed"}
            mlflow.log_metrics({"latency_seconds": time.time() - st, "total_tokens": cb.total_tokens, "quality_score": self._calculate_quality_score(b)})
        yield f"data: {json.dumps({'type': 'complete', 'blueprint': b})}\n\n"
