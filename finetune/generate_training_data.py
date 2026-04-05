"""
generate_training_data.py — Synthetic fine-tuning data generator.

Generates ChatML-format JSONL training pairs for fine-tuning Llama 3.1 8B
as the Protofolio Chairman SME. Uses Gemini Flash as an oracle to produce
high-quality blueprint+verdict outputs from diverse synthetic resume contexts.

Usage (from project root):
    python finetune/generate_training_data.py --num_samples 300

Output:
    finetune/data/train.jsonl   (80%)
    finetune/data/eval.jsonl    (20%)
"""

import os
import sys
import json
import random
import argparse
import time
from pathlib import Path

# Allow running from project root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# ─────────────────────────────────────────────────────────────── #
#  CHAIRMAN SME SYSTEM PROMPT (must match what Flask app uses)    #
# ─────────────────────────────────────────────────────────────── #

SYSTEM_PROMPT = """You are Sophia, the unified Council Chairman and Subject Matter Expert (SME).
You simultaneously embody the perspectives of:
  - Tech Lead   (technical stack, architecture, code quality)
  - UI/UX Designer (visual aesthetics, layout, user experience)
  - Product Manager (market positioning, impact framing, audience clarity)
  - Council Approver (holistic assessment and final decision)

Given a candidate's career goal and their RAG-indexed professional data, produce a
SINGLE valid JSON object. No markdown. No explanation. Only raw JSON.

CRITICAL RULES:
- Extract tech_stack ONLY from the provided context. NEVER invent tools.
- Extract work_experience ONLY from context. NEVER invent company names.
- Extract projects ONLY from context. NEVER invent project names.
- If a field cannot be populated from context, return [] for lists.

Required JSON keys (all required, in this exact structure):
{
  "tagline": "<specific 1-sentence headline for THIS person>",
  "target_role": "<professional title>",
  "tech_stack": ["<tool>", "...up to 10"],
  "work_experience": [{"company": "...", "role": "...", "description": "1-2 sentences"}],
  "projects": [{"name": "...", "description": "1-2 sentences"}],
  "layout_strategy": "<2-3 sentence layout and design philosophy>",
  "template_dif": ["<CSS/HTML tweak>", "...3-5 items"],
  "approval_verdict": {
    "approved": <true|false>,
    "confidence_score": <0.0-1.0>,
    "council_decision": "<APPROVED|CONDITIONAL|REJECTED>",
    "tech_notes": "<tech lead 1-2 sentences>",
    "design_notes": "<designer 1-2 sentences>",
    "market_notes": "<PM 1-2 sentences>",
    "key_strengths": ["<strength>", "...3-5"],
    "gaps_to_address": ["<gap>", "...1-3"]
  }
}"""

# ─────────────────────────────────────────────────────────────── #
#  DIVERSE PERSONA DEFINITIONS & SYNTHETIC RESUME TEMPLATES        #
# ─────────────────────────────────────────────────────────────── #

PERSONAS = [
    "Senior Software Engineer",
    "Frontend Developer",
    "Backend Engineer",
    "Full-Stack Developer",
    "Machine Learning Engineer",
    "Data Scientist",
    "DevOps Engineer",
    "Cloud Solutions Architect",
    "Mobile App Developer",
    "UI/UX Designer",
    "Product Manager",
    "Data Engineer",
    "Cybersecurity Engineer",
    "Site Reliability Engineer",
    "AI Research Engineer",
]

COMPANIES = [
    "Google", "Microsoft", "Amazon", "Meta", "Apple", "Netflix", "Uber", "Airbnb",
    "Stripe", "Shopify", "Atlassian", "Salesforce", "PayPal", "Flipkart", "Swiggy",
    "Zomato", "CRED", "Razorpay", "Groww", "Freshworks", "Zoho", "Infosys", "TCS",
    "Wipro", "HCL", "Accenture", "Cognizant", "Capgemini", "Deloitte", "KPMG",
]

SKILLS_BY_PERSONA = {
    "Senior Software Engineer":       ["Python", "Java", "Go", "Docker", "Kubernetes", "PostgreSQL", "Redis", "AWS", "gRPC", "Kafka"],
    "Frontend Developer":             ["React", "TypeScript", "Next.js", "Tailwind CSS", "Vite", "GraphQL", "Storybook", "Framer Motion", "Cypress", "SCSS"],
    "Backend Engineer":               ["Python", "FastAPI", "Node.js", "PostgreSQL", "MongoDB", "Redis", "Docker", "RabbitMQ", "JWT", "REST API"],
    "Full-Stack Developer":           ["Next.js", "TypeScript", "Node.js", "PostgreSQL", "Prisma", "Docker", "Vercel", "Tailwind CSS", "GraphQL", "React"],
    "Machine Learning Engineer":      ["Python", "PyTorch", "TensorFlow", "Scikit-Learn", "MLflow", "Hugging Face", "LangChain", "Apache Spark", "ONNX", "CUDA"],
    "Data Scientist":                 ["Python", "Pandas", "NumPy", "Scikit-Learn", "SQL", "Tableau", "PySpark", "XGBoost", "Jupyter", "Matplotlib"],
    "DevOps Engineer":                ["Docker", "Kubernetes", "Terraform", "Ansible", "Jenkins", "GitHub Actions", "EKS", "Prometheus", "Grafana", "Helm"],
    "Cloud Solutions Architect":      ["AWS", "Azure", "GCP", "Terraform", "CDK", "Docker", "Kubernetes", "Lambda", "CloudFormation", "VPC"],
    "Mobile App Developer":           ["Flutter", "React Native", "Swift", "Kotlin", "Firebase", "GraphQL", "REST API", "Xcode", "Android Studio", "SQLite"],
    "UI/UX Designer":                 ["Figma", "Adobe XD", "Sketch", "Principle", "Zeplin", "InVision", "Maze", "Prototyping", "Accessibility", "Design Systems"],
    "Product Manager":                ["Jira", "Confluence", "Figma", "SQL", "Mixpanel", "Amplitude", "A/B Testing", "Roadmapping", "User Research", "OKRs"],
    "Data Engineer":                  ["Apache Spark", "dbt", "Airflow", "Kafka", "Snowflake", "BigQuery", "Python", "Postgres", "AWS Glue", "Delta Lake"],
    "Cybersecurity Engineer":         ["Python", "Wireshark", "Metasploit", "Burp Suite", "AWS Security", "SIEM", "OWASP", "Penetration Testing", "IAM", "HashiCorp Vault"],
    "Site Reliability Engineer":      ["Kubernetes", "Prometheus", "Grafana", "Python", "Terraform", "PagerDuty", "ELK Stack", "Chaos Engineering", "SLO", "GitOps"],
    "AI Research Engineer":           ["Python", "PyTorch", "CUDA", "Hugging Face Transformers", "LangChain", "FAISS", "LoRA", "vLLM", "Triton", "MLflow"],
}

PROJECT_TEMPLATES = {
    "Machine Learning Engineer": [
        {"name": "LLM Evaluation Pipeline", "description": "Built an automated benchmark suite for LLMs using Python and PyTorch, evaluating 12 open-source models on custom domain-specific datasets. Reduced evaluation time by 60%."},
        {"name": "Real-Time Sentiment Engine", "description": "Deployed a streaming sentiment analysis system using Apache Kafka and a fine-tuned BERT model, processing 50K messages/sec with 91% accuracy."},
        {"name": "RAG-Powered Knowledge Base", "description": "Built a Retrieval-Augmented Generation system using LangChain, ChromaDB, and Groq, reducing hallucination rate by 73% vs. baseline GPT responses."},
    ],
    "Frontend Developer": [
        {"name": "Design System Library", "description": "Built a 40+ component design system using React, Storybook, and Radix UI, adopted by 5 product teams and reducing design-to-dev handoff time by 45%."},
        {"name": "Real-Time Dashboard", "description": "Developed a live analytics dashboard with WebSockets, Recharts, and Next.js that visualises 1M+ data points with sub-100ms render times."},
        {"name": "Accessibility Audit Tool", "description": "Created a browser extension using TypeScript and WCAG 2.1 guidelines that automatically detects and reports 90% of common accessibility violations."},
    ],
    "DevOps Engineer": [
        {"name": "Multi-Region Kubernetes Platform", "description": "Architected a multi-region EKS cluster with Helm, Terraform, and custom autoscaling policies, supporting 99.99% uptime for 200+ microservices."},
        {"name": "Self-Healing CI/CD Pipeline", "description": "Built a GitOps-based pipeline with GitHub Actions, ArgoCD, and automated rollback policies that reduced deployment failures by 80%."},
        {"name": "Observability Stack", "description": "Deployed a full observability platform using Prometheus, Grafana Loki, and Jaeger across 30+ services, reducing MTTR from 4 hours to 18 minutes."},
    ],
}

# Generic project templates for personas not specifically listed
GENERIC_PROJECTS = [
    {"name": "Cloud-Native API Platform", "description": "Designed and deployed a RESTful API platform with Docker, PostgreSQL, and automated CI/CD, serving 5M+ requests daily with 99.9% uptime."},
    {"name": "Data Analytics Pipeline", "description": "Built an end-to-end data pipeline processing 10GB+ daily using Python and Airflow, reducing reporting latency from 24hrs to 15 minutes."},
    {"name": "Open-Source CLI Tool", "description": "Published an open-source developer productivity tool on GitHub with 800+ stars, 50+ contributors, and 200+ weekly downloads on PyPI."},
]


def generate_context(persona: str) -> str:
    """Generate a synthetic but realistic resume RAG context for a persona."""
    skills = SKILLS_BY_PERSONA.get(persona, ["Python", "SQL", "Docker", "AWS"])
    company1, company2 = random.sample(COMPANIES, 2)
    years1_start = random.randint(2019, 2022)
    years1_end = years1_start + random.randint(1, 2)
    years2_end = years1_end + random.randint(1, 3)

    projects = PROJECT_TEMPLATES.get(persona, GENERIC_PROJECTS)
    proj1, proj2 = random.sample(projects, min(2, len(projects)))

    ctx = f"""Work Experience:
- {company1} ({years1_start}-{years1_end}): {persona}. Led cross-functional engineering initiatives, reducing system latency by {random.randint(20, 60)}%. Mentored {random.randint(2, 5)} junior engineers.
- {company2} ({years1_end}-{years2_end}): Senior {persona}. Owned architecture decisions for a platform serving {random.randint(1, 10)}M+ users. Drove {random.randint(15, 40)}% performance improvement through infrastructure refactoring.

Projects:
- {proj1['name']}: {proj1['description']}
- {proj2['name']}: {proj2['description']}

Skills: {', '.join(skills)}

Education: B.Tech / M.Tech in Computer Science, {random.choice(['IIT Delhi', 'IIT Bombay', 'NIT Trichy', 'BITS Pilani', 'VIT Chennai', 'Anna University'])} ({random.randint(2015, 2020)})

GitHub: {random.randint(20, 150)} public repositories, {random.randint(300, 2500)} total stars, primary languages: {', '.join(random.sample(skills[:5], min(3, len(skills[:5]))))}

LinkedIn: {random.randint(500, 2000)}+ connections, {random.randint(3, 15)} recommendations received.
"""
    return ctx


def generate_blueprint_with_gemini(persona: str, context: str) -> Optional[dict]:
    """Use Gemini Flash (oracle model) to generate a high-quality training blueprint."""
    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
        from langchain_core.messages import SystemMessage, HumanMessage

        model = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            temperature=0.4,
        )
        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=f"Career Goal: {persona}\n\nRAG Context:\n{context}\n\nOutput ONLY the JSON object."),
        ]
        response = model.invoke(messages)
        raw = response.content.strip()

        # Strip markdown fences if present
        if "```json" in raw:
            raw = raw.split("```json")[1].split("```")[0]
        elif "```" in raw:
            raw = raw.split("```")[1].split("```")[0]

        blueprint = json.loads(raw)
        return blueprint
    except Exception as e:
        print(f"  ✗ Gemini call failed: {e}")
        return None


def build_chatml_record(persona: str, context: str, blueprint: dict) -> dict:
    """Wrap a training pair in ChatML format for Unsloth/TRL."""
    return {
        "messages": [
            {"role": "system",    "content": SYSTEM_PROMPT},
            {"role": "user",      "content": f"Career Goal: {persona}\n\nRAG Context:\n{context}\n\nOutput ONLY the JSON object."},
            {"role": "assistant", "content": json.dumps(blueprint, ensure_ascii=False)},
        ]
    }


def main():
    parser = argparse.ArgumentParser(description="Generate fine-tuning data for Protofolio Chairman SME")
    parser.add_argument("--num_samples", type=int, default=300, help="Total training pairs to generate")
    parser.add_argument("--output_dir",  type=str, default="finetune/data", help="Output directory")
    parser.add_argument("--delay",       type=float, default=1.5, help="Seconds between Gemini calls (rate limiting)")
    args = parser.parse_args()

    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("ERROR: GOOGLE_API_KEY not set. Export it before running.")
        sys.exit(1)

    Path(args.output_dir).mkdir(parents=True, exist_ok=True)
    train_path = os.path.join(args.output_dir, "train.jsonl")
    eval_path  = os.path.join(args.output_dir, "eval.jsonl")

    records = []
    failed  = 0

    print(f"\n🚀 Generating {args.num_samples} training pairs across {len(PERSONAS)} personas...\n")

    for i in range(args.num_samples):
        persona = PERSONAS[i % len(PERSONAS)]
        context = generate_context(persona)

        print(f"[{i+1:>4}/{args.num_samples}] Persona: {persona:<35}", end=" ")

        blueprint = generate_blueprint_with_gemini(persona, context)
        if blueprint is None:
            failed += 1
            print("→ SKIPPED")
            continue

        record = build_chatml_record(persona, context, blueprint)
        records.append(record)
        print(f"→ ✓ ({len(blueprint.get('tech_stack', []))} tech, "
              f"verdict={blueprint.get('approval_verdict', {}).get('council_decision', '?')})")

        if args.delay > 0:
            time.sleep(args.delay)

    # 80/20 train/eval split
    random.shuffle(records)
    split = int(len(records) * 0.8)
    train_records = records[:split]
    eval_records  = records[split:]

    with open(train_path, "w", encoding="utf-8") as f:
        for r in train_records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    with open(eval_path, "w", encoding="utf-8") as f:
        for r in eval_records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    print(f"\n✅ Done!")
    print(f"   Training samples : {len(train_records)}  →  {train_path}")
    print(f"   Eval samples     : {len(eval_records)}  →  {eval_path}")
    print(f"   Failed / skipped : {failed}")


# ─── allow Optional without import at top level ───────────────────
from typing import Optional

if __name__ == "__main__":
    main()
