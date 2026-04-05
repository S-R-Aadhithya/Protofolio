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

    def _infer_goal(self, user_id):
        """
        Use an LLM to read the user's resume context from memory and
        automatically determine the best career goal for their portfolio.
        Falls back to a generic goal if inference fails.
        """
        print("DEBUG: No goal provided — inferring from resume context...")
        # Pull a broad context snapshot from memory
        context = self.memory.retrieve_chunks(user_id, "professional experience skills career background")
        if not context or len(context) < 20:
            print("DEBUG: No memory context found, using generic goal.")
            return "Software Engineer"

        try:
            from langchain_groq import ChatGroq
            from langchain_core.prompts import ChatPromptTemplate
            groq_keys = [v for k, v in os.environ.items() if k.startswith("GROQ_API_KEY")]
            api_key = groq_keys[0] if groq_keys else None
            llm = ChatGroq(model="llama-3.1-8b-instant", temperature=0.3, api_key=api_key)
            prompt = ChatPromptTemplate.from_messages([
                ("system", (
                    "You are a career advisor. Based on the resume context below, "
                    "write a single concise career goal sentence (10-20 words) that best represents "
                    "what this person is targeting as their next role. "
                    "Output ONLY the goal sentence, nothing else."
                )),
                ("human", "Resume Context:\n{context}")
            ])
            response = llm.invoke(prompt.format_messages(context=context))
            goal = response.content.strip().strip('"').strip("'")
            print(f"DEBUG: Inferred goal: {goal}")
            return goal
        except Exception as e:
            print(f"WARNING: Goal inference failed: {e}. Using generic fallback.")
            return "Senior Software Engineer"

    @mlflow.trace(name="Council Deliberation Pipeline")
    def deliberate(self, user_id, user_input=None, agent_config=None):
        """
        Run a full council deliberation.

        Args:
            user_id: Unique user identifier for memory retrieval.
            user_input: The portfolio goal. If None, it is automatically inferred from the resume.
            agent_config (dict, optional): Hyperparameter overrides for Optuna tuning.
        """
        # Auto-infer the goal from the resume if not provided
        if not user_input:
            user_input = self._infer_goal(user_id)

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
                o1 = self.tech_lead.get_opinion(context, user_input)
                time.sleep(3)
                o2 = self.designer.get_opinion(context, user_input)
                time.sleep(3)
                o3 = self.pm.get_opinion(context, user_input)
                time.sleep(3)
                opinions = [o1, o2, o3]

                # Stage 2: Reviews
                r1 = self.tech_lead.review(context, opinions)
                time.sleep(3)
                r2 = self.designer.review(context, opinions)
                time.sleep(3)
                r3 = self.pm.review(context, opinions)
                time.sleep(3)
                reviews = [r1, r2, r3]

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
                final_blueprint_str = self.chairman.synthesize(user_input, deliberation_history, context=context)

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
                html_output = render_result["html"] if isinstance(render_result, dict) else str(render_result)
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
            "blueprint": blueprint,
            "inferred_goal": user_input  # always the final resolved goal (inferred or provided)
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
                final_blueprint_str = self.chairman.synthesize(user_input, deliberation_history, context=context)

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

    # ────────────────────────────────────────────────────────────── #
    #  RAG MODE — 2 LLM calls instead of 7 (≈70-80% token savings)  #
    # ────────────────────────────────────────────────────────────── #

    def deliberate_rag(self, user_id, user_input=None, agent_config=None):
        """Token-efficient RAG deliberation: retrieve → Chairman SME → blueprint+verdict."""
        from .rag_ingestor import RAGIngestor

        if not user_input:
            user_input = self._infer_goal(user_id)

        if agent_config:
            self.chairman.update_config(
                temperature=agent_config.get("temperature"),
                model=agent_config.get("model")
            )

        if current_app:
            mlflow.set_tracking_uri(current_app.config.get('MLFLOW_TRACKING_URI', 'file:./mlruns'))
            mlflow.set_experiment(current_app.config.get('MLFLOW_EXPERIMENT_NAME', 'Protofolio_Generation'))
        else:
            mlflow.set_tracking_uri('file:./mlruns')
            mlflow.set_experiment('Protofolio_Generation')
        mlflow.langchain.autolog()

        with mlflow.start_run(run_name=f"RAG_{user_id}"):
            start_time = time.time()

            rag = RAGIngestor()
            context      = rag.retrieve(user_id, user_input, top_k=8)
            chunk_counts = rag.get_chunk_counts(user_id)
            total_chunks = sum(chunk_counts.values())

            if total_chunks == 0:
                print("DEBUG: No RAG chunks — falling back to Mem0.")
                context = self.memory.retrieve_chunks(user_id, user_input)

            mlflow.log_params({
                "mode": "rag",
                "user_input_length": len(user_input),
                "context_length": len(context),
                "rag_chunks_total": total_chunks,
                "chairman_model": self.chairman._model,
                "using_ollama": getattr(self.chairman, "_using_ollama", False),
            })

            with get_openai_callback() as cb:
                result_str = self.chairman.sme_synthesize(user_input, context)

            latency = time.time() - start_time

            try:
                json_str = result_str
                if "```json" in json_str:
                    json_str = json_str.split("```json")[1].split("```")[0]
                elif "```" in json_str:
                    json_str = json_str.split("```")[1].split("```")[0]
                blueprint = json.loads(json_str.strip())
            except Exception:
                blueprint = {"error": "Failed to parse RAG synthesis", "raw": result_str}

            quality_score = self._calculate_quality_score(blueprint)

            try:
                renderer = PortfolioRenderer()
                render_result = renderer.render(blueprint)
                html_output = render_result["html"] if isinstance(render_result, dict) else str(render_result)
            except Exception as e:
                html_output = f"<h1>Render failed</h1><p>{e}</p>"

            mlflow.log_metrics({
                "latency_seconds": latency,
                "total_tokens": cb.total_tokens,
                "prompt_tokens": cb.prompt_tokens,
                "completion_tokens": cb.completion_tokens,
                "quality_score": quality_score,
                "rag_chunks": total_chunks,
            })

            with tempfile.TemporaryDirectory() as tmpdir:
                bp_path = os.path.join(tmpdir, "blueprint.json")
                with open(bp_path, "w", encoding="utf-8") as f:
                    json.dump(blueprint, f, indent=2)
                html_path = os.path.join(tmpdir, "portfolio.html")
                with open(html_path, "w", encoding="utf-8") as f:
                    f.write(html_output)
                mlflow.log_artifacts(tmpdir)

        return {
            "blueprint":       blueprint,
            "inferred_goal":   user_input,
            "rag_mode":        True,
            "chunk_counts":    chunk_counts,
            "finetune_active": getattr(self.chairman, "_using_ollama", False),
        }

    def deliberate_rag_stream(self, user_id, user_input, agent_config=None):
        """SSE generator for RAG mode — emits per-step status then complete."""
        from .rag_ingestor import RAGIngestor

        yield f"data: {json.dumps({'type': 'status', 'agent': 'System', 'message': '⚡ RAG Mode — single-call synthesis...'})}\n\n"

        if current_app:
            mlflow.set_tracking_uri(current_app.config.get('MLFLOW_TRACKING_URI', 'file:./mlruns'))
            mlflow.set_experiment(current_app.config.get('MLFLOW_EXPERIMENT_NAME', 'Protofolio_Generation'))
        else:
            mlflow.set_tracking_uri('file:./mlruns')
            mlflow.set_experiment('Protofolio_Generation')
        mlflow.langchain.autolog()

        with mlflow.start_run(run_name=f"RAGStream_{user_id}"):
            start_time = time.time()

            yield f"data: {json.dumps({'type': 'status', 'agent': 'RAG', 'message': 'Querying ChromaDB vector store...'})}\n\n"

            rag          = RAGIngestor()
            context      = rag.retrieve(user_id, user_input, top_k=8)
            chunk_counts = rag.get_chunk_counts(user_id)
            total_chunks = sum(chunk_counts.values())

            if total_chunks == 0:
                yield f"data: {json.dumps({'type': 'status', 'agent': 'RAG', 'message': 'No indexed data — using Mem0 fallback...'})}\n\n"
                context = self.memory.retrieve_chunks(user_id, user_input)
            else:
                msg = (f"Retrieved {total_chunks} chunks "
                       f"(Resume: {chunk_counts.get('resume',0)}, "
                       f"LinkedIn: {chunk_counts.get('linkedin',0)}, "
                       f"GitHub: {chunk_counts.get('github',0)})")
                yield f"data: {json.dumps({'type': 'rag_chunks', 'chunk_counts': chunk_counts, 'total': total_chunks})}\n\n"
                yield f"data: {json.dumps({'type': 'status', 'agent': 'RAG', 'message': msg})}\n\n"

            if agent_config:
                self.chairman.update_config(
                    temperature=agent_config.get("temperature"),
                    model=agent_config.get("model")
                )

            model_label = (
                os.getenv("OLLAMA_MODEL", "Fine-Tuned")
                if getattr(self.chairman, "_using_ollama", False)
                else "Groq Llama-3.1-8B"
            )
            yield f"data: {json.dumps({'type': 'status', 'agent': 'Chairman SME', 'message': f'Synthesizing via {model_label}...'})}\n\n"

            with get_openai_callback() as cb:
                result_str = self.chairman.sme_synthesize(user_input, context)

            try:
                json_str = result_str
                if "```json" in json_str:
                    json_str = json_str.split("```json")[1].split("```")[0]
                elif "```" in json_str:
                    json_str = json_str.split("```")[1].split("```")[0]
                blueprint = json.loads(json_str.strip())
            except Exception:
                blueprint = {"error": "Failed to parse RAG synthesis"}

            latency       = time.time() - start_time
            quality_score = self._calculate_quality_score(blueprint)
            mlflow.log_metrics({
                "latency_seconds": latency,
                "total_tokens": cb.total_tokens,
                "quality_score": quality_score,
                "rag_chunks": total_chunks,
            })

        yield f"data: {json.dumps({'type': 'complete', 'blueprint': blueprint, 'rag_mode': True, 'chunk_counts': chunk_counts, 'finetune_active': getattr(self.chairman, '_using_ollama', False)})}\n\n"
