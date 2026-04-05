"""
eval_finetuned.py — Compare fine-tuned vs base Chairman model via Ollama.

Metrics: JSON parse rate, field completeness, verdict completeness,
         hallucination rate, ROUGE-L vs oracle.

Usage:
    python finetune/eval_finetuned.py \\
        --eval_file finetune/data/eval.jsonl \\
        --ollama_model protofolio-chairman \\
        --base_model llama3.1
"""
import os, sys, json, argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

REQUIRED_FIELDS = ["tagline","target_role","tech_stack","work_experience",
                   "projects","layout_strategy","template_dif","approval_verdict"]
VERDICT_FIELDS  = ["approved","confidence_score","council_decision","tech_notes",
                   "design_notes","market_notes","key_strengths","gaps_to_address"]

def load_jsonl(path):
    with open(path) as f:
        return [json.loads(l) for l in f if l.strip()]

def call_model(model, sys_p, user_p, host):
    try:
        from langchain_ollama import ChatOllama
        from langchain_core.messages import SystemMessage, HumanMessage
        llm = ChatOllama(model=model, base_url=host, temperature=0.1, num_predict=1500)
        return llm.invoke([SystemMessage(content=sys_p), HumanMessage(content=user_p)]).content
    except Exception as e:
        return f"ERROR: {e}"

def parse_bp(raw):
    try:
        for tag in ["```json", "```"]:
            if tag in raw: raw = raw.split(tag)[1].split("```")[0]
        return json.loads(raw.strip()), None
    except Exception as e:
        return None, str(e)

def scores(bp, ctx, ref_str):
    if not bp: return 0,0,0,1.0,0
    fc = sum(1 for f in REQUIRED_FIELDS if f in bp) / len(REQUIRED_FIELDS)
    vc = sum(1 for f in VERDICT_FIELDS if f in bp.get("approval_verdict",{})) / len(VERDICT_FIELDS)
    companies = [e.get("company","") for e in (bp.get("work_experience") or [])]
    hr = sum(1 for c in companies if c and c.lower() not in ctx.lower()) / max(len(companies),1) if companies else 0
    # simple ROUGE-L
    a,b = json.dumps(bp).lower().split()[:150], ref_str.lower().split()[:150]
    prev = [0]*(len(b)+1)
    for x in a:
        curr = [0]*(len(b)+1)
        for j,y in enumerate(b,1):
            curr[j] = prev[j-1]+1 if x==y else max(prev[j],curr[j-1])
        prev = curr
    lcs = prev[len(b)]
    p = lcs/len(a); r = lcs/len(b)
    rl = 2*p*r/(p+r) if p+r else 0
    return fc, vc, hr, hr, rl

def evaluate(model, sys_p, samples, host, label):
    agg = {"parse":0,"fc":0,"vc":0,"hr":0,"rl":0}
    n = len(samples)
    for i, s in enumerate(samples):
        msgs = s["messages"]
        u = next((m["content"] for m in msgs if m["role"]=="user"),"")
        ref = next((m["content"] for m in msgs if m["role"]=="assistant"),"")
        ctx = u.split("RAG Context:")[-1].strip() if "RAG Context:" in u else ""
        raw = call_model(model, sys_p, u, host)
        bp, err = parse_bp(raw)
        if bp:
            agg["parse"] += 1
            fc,vc,_,hr,rl = scores(bp, ctx, ref)
            agg["fc"]+=fc; agg["vc"]+=vc; agg["hr"]+=hr; agg["rl"]+=rl
        else:
            agg["hr"] += 1.0
        print(f"\r  [{label}] {i+1}/{n}", end="", flush=True)
    print()
    return {k: v/n for k,v in agg.items()}

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--eval_file",    default="finetune/data/eval.jsonl")
    p.add_argument("--ollama_model", default="protofolio-chairman")
    p.add_argument("--base_model",   default="llama3.1")
    p.add_argument("--ollama_host",  default="http://localhost:11434")
    p.add_argument("--n_samples",    type=int, default=50)
    p.add_argument("--mlflow_uri",   default="file:./mlruns")
    args = p.parse_args()

    samples = load_jsonl(args.eval_file)
    if args.n_samples > 0: samples = samples[:args.n_samples]
    sys_p = samples[0]["messages"][0]["content"]

    print(f"\n🧪 Evaluating {len(samples)} samples | FT={args.ollama_model} vs Base={args.base_model}\n")
    ft   = evaluate(args.ollama_model, sys_p, samples, args.ollama_host, "Fine-Tuned    ")
    base = evaluate(args.base_model,   sys_p, samples, args.ollama_host, "Base-Model    ")

    print(f"\n{'='*60}")
    print(f"  {'Metric':<25} {'Fine-Tuned':>12} {'Base':>12}")
    print(f"{'='*60}")
    labels = {"parse":"Parse Success","fc":"Field Completeness","vc":"Verdict Completeness",
              "hr":"Hallucination Rate↓","rl":"ROUGE-L"}
    for k, lbl in labels.items():
        print(f"  {lbl:<25} {ft[k]:>12.3f} {base[k]:>12.3f}")
    print(f"{'='*60}\n")

    try:
        import mlflow
        mlflow.set_tracking_uri(args.mlflow_uri)
        mlflow.set_experiment("FineTune_Eval")
        with mlflow.start_run(run_name=f"{args.ollama_model}_vs_{args.base_model}"):
            mlflow.log_params({"ft_model": args.ollama_model, "base_model": args.base_model, "n": len(samples)})
            for k,v in ft.items():   mlflow.log_metric(f"ft_{k}", v)
            for k,v in base.items(): mlflow.log_metric(f"base_{k}", v)
        print("✅ Logged to MLflow (FineTune_Eval experiment).\n")
    except Exception as e:
        print(f"WARNING: MLflow failed: {e}\n")

if __name__ == "__main__":
    main()
