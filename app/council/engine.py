from .agents import TechLead, Designer, ProductManager, Chairman
from .memory import MemoryManager
from ..generator.renderer import PortfolioRenderer
from flask import current_app
import time
import mlflow
import json
import os
import tempfile

try:
    from langchain.callbacks import get_openai_callback
except ImportError:
    from langchain_community.callbacks.manager import get_openai_callback

class CouncilEngine:
    def __init__(self):
        self.tech_lead = TechLead()
        self.designer = Designer()
        self.pm = ProductManager()
        self.chairman = Chairman()
        self.memory = MemoryManager()

    def _calculate_quality_score(self, blueprint):
        """Calculate a heuristic portfolio quality score based on completeness."""
        score = 0
        if isinstance(blueprint, dict) and "error" not in blueprint:
            if blueprint.get("tagline"): score += 20
            if blueprint.get("tech_stack"): score += 20
            if getattr(blueprint, "get", lambda x: None)("layout_strategy"): score += 20
            projects = blueprint.get("projects", [])
            num_projects = len(projects) if isinstance(projects, list) else 0
            score += min(40, num_projects * 20)
        return score

    @mlflow.trace(name="Council Deliberation Pipeline")
    def deliberate(self, user_id, user_input, agent_config=None):
        """
        Run a full council deliberation.

        Args:
            user_id: Unique user identifier for memory retrieval.
            user_input: The user's portfolio goal.
            agent_config (dict, optional): Hyperparameter overrides for Optuna tuning.
                Keys: 'temperature' (float), 'model' (str)
        """
        print(f"DEBUG: Starting deliberation for user {user_id} with goal: {user_input}")

        # Apply agent_config overrides (used by Optuna tuner)
        if agent_config:
            temperature = agent_config.get("temperature")
            model = agent_config.get("model")
            for agent in [self.tech_lead, self.designer, self.pm, self.chairman]:
                agent.update_config(temperature=temperature, model=model)

        # Setup MLflow from app config if available
        if current_app:
            tracking_uri = current_app.config.get('MLFLOW_TRACKING_URI', 'file:./mlruns')
            experiment_name = current_app.config.get('MLFLOW_EXPERIMENT_NAME', 'Protofolio_Generation')
            mlflow.set_tracking_uri(tracking_uri)
            mlflow.set_experiment(experiment_name)
        else:
            mlflow.set_tracking_uri('file:./mlruns')
            mlflow.set_experiment('Protofolio_Generation')

        # Enable MLflow LLM Auto-Tracing for Langchain
        mlflow.langchain.autolog()

        with mlflow.start_run(run_name=f"Deliberate_{user_id}"):
            start_time = time.time()

            # Retrieve RAG Context from Mem0
            print("DEBUG: Retrieving memory chunks...")
            context = self.memory.retrieve_chunks(user_id, user_input)
            print(f"DEBUG: Retrieved context: {len(context)} chars")

            # Determine active temperature/model (post-config or defaults)
            active_temperature = self.tech_lead._temperature
            active_model = self.tech_lead._model

            # Log Parameters
            mlflow.log_params({
                "user_input_length": len(user_input),
                "resume_complexity_chars": len(context),
                "temperature": active_temperature,
                "tech_lead_model": active_model,
                "designer_model": self.designer._model,
                "pm_model": self.pm._model,
                "chairman_model": self.chairman._model,
            })

            with get_openai_callback() as cb:
                # Stage 1: Opinions
                opinions = [
                    self.tech_lead.get_opinion(context, user_input),
                    self.designer.get_opinion(context, user_input),
                    self.pm.get_opinion(context, user_input)
                ]

                # Stage 2: Reviews
                reviews = [
                    self.tech_lead.review(context, opinions),
                    self.designer.review(context, opinions),
                    self.pm.review(context, opinions)
                ]

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

            latency = time.time() - start_time

            # Try to parse JSON from synthesis
            try:
                json_str = final_blueprint_str
                if "```json" in json_str:
                    json_str = json_str.split("```json")[1].split("```")[0]
                elif "```" in json_str:
                    json_str = json_str.split("```")[1].split("```")[0]
                blueprint = json.loads(json_str)
            except Exception:
                blueprint = {"error": "Failed to parse synthesis", "raw": final_blueprint_str}

            quality_score = self._calculate_quality_score(blueprint)

            # Generate HTML Portfolio Artifact
            try:
                renderer = PortfolioRenderer()
                render_result = renderer.render(blueprint)
                html_output = render_result.get("html", "")
            except Exception as e:
                html_output = f"<h1>Failed to render HTML</h1><p>{str(e)}</p>"

            # Log Metrics
            mlflow.log_metrics({
                "latency_seconds": latency,
                "total_tokens": cb.total_tokens,
                "prompt_tokens": cb.prompt_tokens,
                "completion_tokens": cb.completion_tokens,
                "quality_score": quality_score
            })

            # Log Artifacts
            with tempfile.TemporaryDirectory() as tmpdir:
                delib_path = os.path.join(tmpdir, "deliberation_log.txt")
                with open(delib_path, "w", encoding="utf-8") as f:
                    f.write(deliberation_history)

                blueprint_path = os.path.join(tmpdir, "blueprint.json")
                with open(blueprint_path, "w", encoding="utf-8") as f:
                    json.dump(blueprint, f, indent=2)

                html_path = os.path.join(tmpdir, "portfolio.html")
                with open(html_path, "w", encoding="utf-8") as f:
                    f.write(html_output)

                mlflow.log_artifacts(tmpdir)

        return {
            "deliberation": deliberation_history,
            "blueprint": blueprint
        }

    def deliberate_stream(self, user_id, user_input, agent_config=None):
        """Generator yielding SSE strings for live portfolio generation."""
        yield f"data: {json.dumps({'type': 'status', 'agent': 'System', 'message': 'Initializing Council...'})}\n\n"
        
        # Setup MLflow from app config if available
        if current_app:
            tracking_uri = current_app.config.get('MLFLOW_TRACKING_URI', 'file:./mlruns')
            experiment_name = current_app.config.get('MLFLOW_EXPERIMENT_NAME', 'Protofolio_Generation')
            mlflow.set_tracking_uri(tracking_uri)
            mlflow.set_experiment(experiment_name)
        else:
            mlflow.set_tracking_uri('file:./mlruns')
            mlflow.set_experiment('Protofolio_Generation')

        mlflow.langchain.autolog()

        with mlflow.start_run(run_name=f"Stream_Deliberate_{user_id}"):
            start_time = time.time()

            yield f"data: {json.dumps({'type': 'status', 'agent': 'Memory', 'message': 'Retrieving context from Mem0...'})}\n\n"
            context = self.memory.retrieve_chunks(user_id, user_input)

            if agent_config:
                temperature = agent_config.get("temperature")
                model = agent_config.get("model")
                for agent in [self.tech_lead, self.designer, self.pm, self.chairman]:
                    agent.update_config(temperature=temperature, model=model)

            with get_openai_callback() as cb:
                yield f"data: {json.dumps({'type': 'status', 'agent': 'Tech Lead', 'message': 'Drafting technical opinion...'})}\n\n"
                tech_opinion = self.tech_lead.get_opinion(context, user_input)
                
                yield f"data: {json.dumps({'type': 'status', 'agent': 'Designer', 'message': 'Drafting design layout...'})}\n\n"
                designer_opinion = self.designer.get_opinion(context, user_input)
                
                yield f"data: {json.dumps({'type': 'status', 'agent': 'Product Manager', 'message': 'Drafting product strategy...'})}\n\n"
                pm_opinion = self.pm.get_opinion(context, user_input)

                opinions = [tech_opinion, designer_opinion, pm_opinion]

                yield f"data: {json.dumps({'type': 'status', 'agent': 'Tech Lead', 'message': 'Reviewing peers...'})}\n\n"
                tech_review = self.tech_lead.review(context, opinions)
                
                yield f"data: {json.dumps({'type': 'status', 'agent': 'Designer', 'message': 'Reviewing styling...'})}\n\n"
                designer_review = self.designer.review(context, opinions)
                
                yield f"data: {json.dumps({'type': 'status', 'agent': 'Product Manager', 'message': 'Reviewing market fit...'})}\n\n"
                pm_review = self.pm.review(context, opinions) 

                reviews = [tech_review, designer_review, pm_review]

                deliberation_history = "--- INITIAL OPINIONS ---\n"
                for i, op in enumerate(opinions):
                    deliberation_history += f"Agent {i} Original: {op}\n\n"
                deliberation_history += "--- REVIEWS ---\n"
                for i, r in enumerate(reviews):
                    deliberation_history += f"Agent {i} Review: {r}\n\n"

                yield f"data: {json.dumps({'type': 'status', 'agent': 'Chairman', 'message': 'Synthesizing final blueprint...'})}\n\n"
                final_blueprint_str = self.chairman.synthesize(user_input, deliberation_history)

            try:
                json_str = final_blueprint_str
                if "```json" in json_str: json_str = json_str.split("```json")[1].split("```")[0]
                elif "```" in json_str: json_str = json_str.split("```")[1].split("```")[0]
                blueprint = json.loads(json_str)
            except Exception:
                blueprint = {"error": "Failed to parse synthesis"}
                
            latency = time.time() - start_time
            quality_score = self._calculate_quality_score(blueprint)

            mlflow.log_metrics({
                "latency_seconds": latency,
                "total_tokens": cb.total_tokens,
                "quality_score": quality_score
            })

        yield f"data: {json.dumps({'type': 'complete', 'blueprint': blueprint})}\n\n"
