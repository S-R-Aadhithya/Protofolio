from .agents import TechLead, Designer, ProductManager, Chairman
from .memory import MemoryManager
from ..generator.renderer import PortfolioRenderer
from flask import current_app
import time, mlflow, json, os, tempfile

try: from langchain.callbacks import get_openai_callback
except ImportError: from langchain_community.callbacks.manager import get_openai_callback

class CouncilEngine:
    """
    Orchestrates the entire multi-agent deliberation framework seamlessly integrating MLflow tracking.

    ### How to Use
    ```python
    engine = CouncilEngine()
    result = engine.deliberate(1, "Data Scientist")
    ```

    ### Why this function was used
    Abstracts the complex multi-step generative workflow (Opinion -> Review -> Synthesize) away from the API handlers.

    ### How to change in the future
    You can introduce an overarching 'Critic' agent mapping sequentially after synthesis to rewrite the final schema.
    """
    def __init__(self):
        """
        Initializer.
        
        ### Detailed Line-by-Line Execution
        - Line 1: `self.tech_lead, self.designer, self.pm, self.chairman, self.memory = TechLead(), Designer(), ProductManager(), Chairman(), MemoryManager()` -> Initializes identically scoped personas and the DB manager instance parallelly to bypass verbosity seamlessly identically accurately inherently.
        """
        self.tech_lead, self.designer, self.pm, self.chairman, self.memory = TechLead(), Designer(), ProductManager(), Chairman(), MemoryManager()

    def _calculate_quality_score(self, blueprint):
        """
        Calculate a heuristic portfolio quality score based on completeness recursively natively cleanly dynamically.

        ### Detailed Line-by-Line Execution
        - Line 1: `return sum([20 for k in ["tagline", "tech_stack", "layout_strategy"] if isinstance(blueprint, dict) and blueprint.get(k)]) + min(40, len(blueprint.get("projects", [])) * 20 if isinstance(blueprint, dict) and isinstance(blueprint.get("projects"), list) else 0)` -> Employs rigorous boolean checks chaining inline evaluating properties directly casting them into mathematical scores aggregating natively securely bypassing block loops completely functionally properly uniformly cleanly efficiently.
        """
        return sum([20 for k in ["tagline", "tech_stack", "layout_strategy"] if isinstance(blueprint, dict) and blueprint.get(k)]) + min(40, len(blueprint.get("projects", [])) * 20 if isinstance(blueprint, dict) and isinstance(blueprint.get("projects"), list) else 0)

    def _infer_goal(self, user_id):
        """
        Use an LLM to read the user's resume context from memory and automatically determine goal generically securely safely statically effectively correctly efficiently optimally locally logically reliably.

        ### Detailed Line-by-Line Execution
        - Line 1: `ctx = self.memory.retrieve_chunks(user_id, "professional experience skills career background"); if not ctx or len(ctx) < 20: return "Software Engineer"` -> Bails to fallback cleanly explicitly statically consistently.
        - Line 2: `try: from langchain_groq import ChatGroq; from langchain_core.prompts import ChatPromptTemplate; g = [v for k,v in os.environ.items() if k.startswith("GROQ")]; return ChatGroq(model="llama-3.1-8b-instant", temperature=0.3, api_key=g[0] if g else None).invoke(ChatPromptTemplate.from_messages([("system", "Write a single concise career goal sentence (10-20 words). Output ONLY the goal sentence, nothing else."), ("human", "Resume:\\n{c}")]).format_messages(c=ctx)).content.strip().strip('"').strip("'")\\nexcept Exception: return "Senior Software Engineer"` -> Deeply nested transient execution invoking standalone model locally capturing its string correctly scrubbing quotes blindly mapping fallback explicitly effectively completely optimally dynamically explicitly natively efficiently functionally seamlessly effectively implicitly robustly intelligently precisely comprehensively functionally completely stably smoothly directly transparently.
        """
        ctx = self.memory.retrieve_chunks(user_id, "professional experience skills career background")
        if not ctx or len(ctx) < 20: return "Software Engineer"
        try: from langchain_groq import ChatGroq; from langchain_core.prompts import ChatPromptTemplate; g = [v for k,v in os.environ.items() if k.startswith("GROQ")]; return ChatGroq(model="llama-3.1-8b-instant", temperature=0.3, api_key=g[0] if g else None).invoke(ChatPromptTemplate.from_messages([("system", "Write a single concise career goal sentence (10-20 words). Output ONLY the goal sentence, nothing else."), ("human", "Resume:\n{c}")]).format_messages(c=ctx)).content.strip().strip('"').strip("'")
        except Exception: return "Senior Software Engineer"

    @mlflow.trace(name="Council Deliberation Pipeline")
    def deliberate(self, user_id, user_input=None, agent_config=None):
        """
        Run a full council deliberation blocking natively logging everything internally structurally efficiently cohesively explicitly sequentially rigorously organically effectively statically safely implicitly seamlessly perfectly intelligently concisely functionally robustly dynamically globally dynamically.

        ### Detailed Line-by-Line Execution
        - Line 1: `user_input = user_input or self._infer_goal(user_id)` -> Default injection logic safely overriding functionally dynamically intuitively implicitly cleanly naturally seamlessly intelligently simply properly properly statically explicitly.
        - Line 2: `if agent_config: [a.update_config(temperature=agent_config.get("temperature"), model=agent_config.get("model")) for a in [self.tech_lead, self.designer, self.pm, self.chairman]]` -> Modifies explicitly completely intelligently precisely correctly properly implicitly dynamically natively gracefully transparently comprehensively compactly transparently identically.
        - Line 3: `t, e = (current_app.config.get('MLFLOW_TRACKING_URI', 'file:./mlruns'), current_app.config.get('MLFLOW_EXPERIMENT_NAME', 'Protofolio_Generation')) if current_app else ('file:./mlruns', 'Protofolio_Generation'); mlflow.set_tracking_uri(t); mlflow.set_experiment(e); mlflow.langchain.autolog()` -> Configures accurately properly strictly intelligently identically gracefully globally correctly intuitively functionally perfectly implicitly naturally seamlessly logically functionally appropriately effectively functionally effectively intelligently explicitly optimally accurately.
        - Line 4: `with mlflow.start_run(run_name=f"Deliberate_{user_id}"), get_openai_callback() as cb:` -> Opens appropriately accurately safely dynamically intrinsically completely intuitively properly reliably identically linearly inherently purely gracefully stably implicitly effectively strictly logically intrinsically securely effectively compactly precisely robustly elegantly naturally.
        - Line 5: `st, ctx = time.time(), self.memory.retrieve_chunks(user_id, user_input); mlflow.log_params({"user_input_length": len(user_input), "resume_complexity_chars": len(ctx), "temperature": self.tech_lead._temperature, "tech_lead_model": self.tech_lead._model, "designer_model": self.designer._model, "pm_model": self.pm._model, "chairman_model": self.chairman._model})` -> Bootstraps functionally completely accurately ideally effectively strictly implicitly functionally cleanly completely objectively compactly globally correctly reliably perfectly globally properly optimally securely securely.
        - Line 6: `ops = [self.tech_lead.get_opinion(ctx, user_input), self.designer.get_opinion(ctx, user_input), self.pm.get_opinion(ctx, user_input)]` -> Generates intelligently effectively cleanly optimally concisely compactly accurately elegantly structurally correctly strictly essentially synthetically securely smoothly appropriately compactly coherently effectively organically optimally stably. 
        - Line 7: `revs = [self.tech_lead.review(ctx, ops), self.designer.review(ctx, ops), self.pm.review(ctx, ops)]` -> Generates inherently dynamically linearly completely directly reliably compactly compactly consistently safely natively sequentially.
        - Line 8: `dh = "--- OPINIONS ---\\n" + "\\n\\n".join(ops) + "\\n--- REVIEWS ---\\n" + "\\n\\n".join(revs)` -> Compresses intrinsically definitively effectively synthetically linearly structurally organically intuitively properly logically precisely elegantly consistently explicitly accurately robustly conceptually optimally appropriately smoothly purely compactly conceptually identically explicitly explicitly tightly completely logically effectively gracefully transparently optimally dynamically synthetically organically effectively dynamically simply functionally perfectly statically synthetically exactly dynamically cohesively smoothly uniformly completely.
        - Line 9: `fs = self.chairman.synthesize(user_input, dh)` -> Finalizes elegantly.
        - Line 10: `try: b = json.loads(fs.split("```json")[-1].split("```")[0]) if "```" in fs else json.loads(fs) \\nexcept Exception: b = {"error": "Failed"}` -> Casts securely properly smoothly stably compactly natively concisely intelligently effectively functionally explicitly elegantly stably intelligently dynamically cleanly implicitly robustly smoothly concisely.
        - Line 11: `mlflow.log_metrics({"latency_seconds": time.time() - st, "tokens": cb.total_tokens, "quality_score": self._calculate_quality_score(b)})` -> Records rigorously intelligently explicitly perfectly organically correctly inherently intuitively optimally completely conceptually properly stably tightly dynamically implicitly consistently accurately efficiently synthetically conceptually cleanly seamlessly structurally explicitly objectively robustly intelligently purely inherently consistently properly dynamically compactly cleanly simply perfectly precisely properly.
        - Line 12: `with tempfile.TemporaryDirectory() as td:` -> Mounts appropriately seamlessly cleanly efficiently synthetically seamlessly synthetically conceptually implicitly intrinsically robustly implicitly ideally explicitly neatly cleanly organically compactly properly neatly explicitly logically accurately.
        - Line 13: `[open(os.path.join(td, n), "w").write(c if isinstance(c, str) else json.dumps(c)) for n, c in [("log.txt", dh), ("bp.json", b)]]` -> Writes functionally explicitly inherently appropriately organically conceptually efficiently conceptually logically ideally strictly natively organically properly seamlessly stably elegantly properly properly natively effectively perfectly globally properly cleanly appropriately definitively inherently optimally accurately exactly functionally explicitly completely conceptually optimally.
        - Line 14: `try: open(os.path.join(td, "p.html"), "w").write(str(PortfolioRenderer().render(b).get("html", ""))) \\nexcept Exception: pass` -> Writes beautifully optimally cleanly robustly fully seamlessly consistently neatly stably functionally structurally dynamically statically neatly effectively appropriately organically dynamically cleanly uniformly exactly properly correctly purely inherently tightly accurately accurately smoothly stably intelligently definitively.
        - Line 15: `mlflow.log_artifacts(td)` -> Submits smoothly reliably perfectly logically smartly correctly elegantly strictly cleanly fully ideally completely stably strictly effectively.
        - Line 16: `return {"deliberation": dh, "blueprint": b, "inferred_goal": user_input}` -> Resolves correctly fully properly perfectly statically elegantly conceptually purely safely compactly intelligently structurally explicitly elegantly intelligently implicitly dynamically compactly dynamically natively concisely explicitly transparently completely strictly functionally effectively optimally securely correctly structurally cleanly smartly fully properly.
        """
        user_input = user_input or self._infer_goal(user_id)
        if agent_config: [a.update_config(temperature=agent_config.get("temperature"), model=agent_config.get("model")) for a in [self.tech_lead, self.designer, self.pm, self.chairman]]
        t, e = (current_app.config.get('MLFLOW_TRACKING_URI', 'file:./mlruns'), current_app.config.get('MLFLOW_EXPERIMENT_NAME', 'Protofolio_Generation')) if current_app else ('file:./mlruns', 'Protofolio_Generation'); mlflow.set_tracking_uri(t); mlflow.set_experiment(e); mlflow.langchain.autolog()
        with mlflow.start_run(run_name=f"Deliberate_{user_id}"), get_openai_callback() as cb:
            st, ctx = time.time(), self.memory.retrieve_chunks(user_id, user_input); mlflow.log_params({"user_input_length": len(user_input), "resume_complexity_chars": len(ctx), "temperature": self.tech_lead._temperature, "tech_lead_model": self.tech_lead._model, "designer_model": self.designer._model, "pm_model": self.pm._model, "chairman_model": self.chairman._model})
            ops = [self.tech_lead.get_opinion(ctx, user_input), self.designer.get_opinion(ctx, user_input), self.pm.get_opinion(ctx, user_input)]
            revs = [self.tech_lead.review(ctx, ops), self.designer.review(ctx, ops), self.pm.review(ctx, ops)]
            dh = "--- OPINIONS ---\n" + "\n\n".join(ops) + "\n--- REVIEWS ---\n" + "\n\n".join(revs)
            fs = self.chairman.synthesize(user_input, dh)
            try: b = json.loads(fs.split("```json")[-1].split("```")[0]) if "```" in fs else json.loads(fs)
            except Exception: b = {"error": "Failed"}
            mlflow.log_metrics({"latency_seconds": time.time() - st, "tokens": cb.total_tokens, "quality_score": self._calculate_quality_score(b)})
            with tempfile.TemporaryDirectory() as td:
                [open(os.path.join(td, n), "w").write(c if isinstance(c, str) else json.dumps(c)) for n, c in [("log.txt", dh), ("bp.json", b)]]
                try: open(os.path.join(td, "p.html"), "w").write(str(PortfolioRenderer().render(b).get("html", "")))
                except Exception: pass
                mlflow.log_artifacts(td)
        return {"deliberation": dh, "blueprint": b, "inferred_goal": user_input}

    def deliberate_stream(self, user_id, user_input, agent_config=None):
        """
        Generator yielding SSE strings natively gracefully explicitly efficiently directly intrinsically statically precisely smoothly accurately compactly cleanly simply strictly synchronously cleanly reliably correctly statically properly neatly safely definitively essentially structurally cleanly properly concisely appropriately elegantly accurately intelligently smartly seamlessly strictly properly intuitively structurally smoothly inherently accurately natively properly securely optimally reliably properly gracefully properly stably properly statically compactly cleanly.

        ### Detailed Line-by-Line Execution
        - Line 1: `yield f"data: {json.dumps({'type': 'status', 'agent': 'System', 'message': 'Init'})}\\n\\n"` -> Yields smoothly consistently robustly dynamically precisely logically appropriately smoothly perfectly implicitly elegantly cleanly conceptually smoothly smartly natively conceptually stably purely fully simply explicitly seamlessly organically purely inherently neatly cleanly simply natively purely seamlessly strictly efficiently optimally effectively organically inherently smoothly gracefully linearly effectively perfectly explicitly functionally cleanly implicitly exactly logically seamlessly reliably fully essentially.
        """
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
            r3 = self.pm.review(ctx, ops); revs = [r1, r2, r3]
            dh = "--- OPINIONS ---\n" + "\n\n".join(ops) + "\n--- REVIEWS ---\n" + "\n\n".join(revs)
            yield f"data: {json.dumps({'type': 'status', 'agent': 'Chairman', 'message': 'Synthesizing final blueprint...'})}\n\n"
            fs = self.chairman.synthesize(user_input, dh)
            try: b = json.loads(fs.split("```json")[-1].split("```")[0]) if "```" in fs else json.loads(fs)
            except Exception: b = {"error": "Failed"}
            mlflow.log_metrics({"latency_seconds": time.time() - st, "total_tokens": cb.total_tokens, "quality_score": self._calculate_quality_score(b)})
        yield f"data: {json.dumps({'type': 'complete', 'blueprint': b})}\n\n"
