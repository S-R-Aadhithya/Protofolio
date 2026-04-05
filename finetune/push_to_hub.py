"""
push_to_hub.py — Upload LoRA adapter to HuggingFace Hub.

Creates a versioned HF repo with:
  - LoRA adapter weights
  - tokenizer config
  - README with Ollama setup instructions

Usage:
    export HUGGINGFACE_TOKEN=hf_xxxxxxxxx
    python finetune/push_to_hub.py \\
        --adapter_dir finetune/lora_adapter \\
        --repo_id     your-username/protofolio-chairman-lora
"""

import os
import sys
import argparse
from pathlib import Path

README_TEMPLATE = """# Protofolio Chairman SME — LoRA Adapter

Fine-tuned **Llama 3.1 8B Instruct** adapter for the Protofolio portfolio generation platform.

## What It Does
This adapter trains the model to act as the unified Chairman SME council member:
- Tech Lead (technical stack assessment)
- UI/UX Designer (layout and aesthetic recommendations)
- Product Manager (market positioning)
- Council Approver (holistic approval verdict)

Given a candidate's RAG context (resume + LinkedIn + GitHub), it outputs a structured JSON blueprint
with portfolio configuration AND an approval verdict.

## Base Model
`unsloth/Meta-Llama-3.1-8B-Instruct`

## Deployment via Ollama

```bash
# 1. Download GGUF from this repo or generate from the adapter
# 2. Create a Modelfile
cat > Modelfile << 'EOF'
FROM ./model-Q4_K_M.gguf
SYSTEM "You are Sophia, the unified Council Chairman and Subject Matter Expert (SME)..."
PARAMETER temperature 0.3
PARAMETER num_predict 1500
EOF

# 3. Create the Ollama model
ollama create protofolio-chairman -f Modelfile

# 4. Set env vars in your Protofolio .env
OLLAMA_MODEL=protofolio-chairman
OLLAMA_HOST=http://localhost:11434
```

## Load as HuggingFace PEFT Adapter

```python
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer

base = AutoModelForCausalLM.from_pretrained("meta-llama/Meta-Llama-3.1-8B-Instruct", load_in_4bit=True)
model = PeftModel.from_pretrained(base, "{repo_id}")
tokenizer = AutoTokenizer.from_pretrained("{repo_id}")
```

## Training Details
- Method: QLoRA (4-bit) with Unsloth
- LoRA rank: 16, alpha: 32
- Training data: Synthetic portfolio blueprints across 15 career personas
- Task: Instruction-following for structured JSON blueprint generation
"""


def main():
    parser = argparse.ArgumentParser(description="Push fine-tuned LoRA adapter to HuggingFace Hub")
    parser.add_argument("--adapter_dir", default="finetune/lora_adapter", help="Path to saved LoRA adapter")
    parser.add_argument("--repo_id",     required=True, help="HF repo, e.g. username/protofolio-chairman-lora")
    parser.add_argument("--private",     action="store_true", help="Create as private repository")
    args = parser.parse_args()

    token = os.getenv("HUGGINGFACE_TOKEN") or os.getenv("HF_TOKEN")
    if not token:
        print("ERROR: Set HUGGINGFACE_TOKEN environment variable.")
        sys.exit(1)

    if not Path(args.adapter_dir).exists():
        print(f"ERROR: Adapter directory not found: {args.adapter_dir}")
        sys.exit(1)

    try:
        from huggingface_hub import HfApi, create_repo
    except ImportError:
        print("ERROR: pip install huggingface_hub")
        sys.exit(1)

    try:
        from peft import PeftModel
        from transformers import AutoTokenizer
    except ImportError:
        print("ERROR: pip install peft transformers")
        sys.exit(1)

    api = HfApi(token=token)

    # Create repo
    print(f"\n🔧 Creating HuggingFace repo: {args.repo_id} (private={args.private})")
    create_repo(
        repo_id  = args.repo_id,
        token    = token,
        private  = args.private,
        exist_ok = True,
    )

    # Upload adapter files
    print(f"\n📤 Uploading adapter from: {args.adapter_dir}")
    api.upload_folder(
        folder_path = args.adapter_dir,
        repo_id     = args.repo_id,
        repo_type   = "model",
        token       = token,
    )

    # Write README
    readme_content = README_TEMPLATE.format(repo_id=args.repo_id)
    api.upload_file(
        path_or_fileobj = readme_content.encode("utf-8"),
        path_in_repo    = "README.md",
        repo_id         = args.repo_id,
        repo_type       = "model",
        token           = token,
    )

    print(f"\n✅ Upload complete!")
    print(f"   Adapter URL: https://huggingface.co/{args.repo_id}")
    print(f"\n💡 To use in Protofolio, set in .env:")
    print(f"   HF_ADAPTER_REPO={args.repo_id}")


if __name__ == "__main__":
    main()
