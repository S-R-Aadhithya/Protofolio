"""
train_lora.py — Cross-platform fine-tuning for Protofolio Chairman SME.

Supports:
1. NVIDIA GPU (CUDA): Uses Unsloth (4x faster, memory efficient).
2. Apple Silicon (MPS): Fallback to standard HF PEFT + Transformers.
3. CPU: Basic fallback (extremely slow, for debugging).

Usage:
    python finetune/train_lora.py \
        --train_file finetune/data/train.jsonl \
        --eval_file  finetune/data/eval.jsonl  \
        --output_dir finetune/lora_adapter      \
        --epochs 3
"""

import os
import sys
import json
import argparse
import torch
from pathlib import Path
from dotenv import load_dotenv

# Load GOOGLE_API_KEY if present (though not strictly needed for training)
load_dotenv()

# ─────────────────────────────────────────────────────────────── #
#  CONFIG                                                           #
# ─────────────────────────────────────────────────────────────── #

BASE_MODEL   = "unsloth/Meta-Llama-3.1-8B-Instruct"   # 4-bit pre-quantized for CUDA
BASE_MODEL_HF = "meta-llama/Meta-Llama-3.1-8B-Instruct" # Standard HF model for MPS
MAX_SEQ_LEN  = 2048
LORA_RANK    = 16
LORA_ALPHA   = 32
LORA_DROPOUT = 0.05
TARGET_MODULES = ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]

def get_device():
    if torch.cuda.is_available():
        return "cuda"
    elif torch.backends.mps.is_available():
        return "mps"
    return "cpu"


def load_jsonl(path: str):
    """Load JSONL file into a list of dicts."""
    records = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def format_chatml(sample: dict, tokenizer) -> dict:
    """
    Convert a ChatML dict ({"messages": [...]}) into a tokenized record.
    Unsloth's apply_chat_template handles the special tokens automatically.
    """
    text = tokenizer.apply_chat_template(
        sample["messages"],
        tokenize=False,
        add_generation_prompt=False,
    )
    return {"text": text}


def main():
    parser = argparse.ArgumentParser(description="QLoRA fine-tuning for Protofolio Chairman")
    parser.add_argument("--train_file",  default="finetune/data/train.jsonl")
    parser.add_argument("--eval_file",   default="finetune/data/eval.jsonl")
    parser.add_argument("--output_dir",  default="finetune/lora_adapter")
    parser.add_argument("--epochs",      type=int,   default=3)
    parser.add_argument("--batch_size",  type=int,   default=2)
    parser.add_argument("--grad_accum",  type=int,   default=4,  help="Gradient accumulation steps (effective batch = batch × accum)")
    parser.add_argument("--lr",          type=float, default=2e-4)
    parser.add_argument("--warmup_ratio",type=float, default=0.03)
    parser.add_argument("--save_gguf",   action="store_true", help="Export GGUF after training (for Ollama)")
    parser.add_argument("--gguf_quant",  default="q4_k_m",    help="GGUF quantization level (q4_k_m recommended)")
    args = parser.parse_args()

    # ── 1. Load model + tokenizer ──────────────────────────────────────── #
    device = get_device()
    print(f"\n{'='*60}")
    print(f"  Protofolio Chairman Fine-Tuning")
    print(f"  Detected Device: {device.upper()}")
    print(f"  LoRA rank  : {LORA_RANK}")
    print(f"  Epochs     : {args.epochs}")
    print(f"{'='*60}\n")

    use_unsloth = False
    if device == "cuda":
        try:
            from unsloth import FastLanguageModel
            use_unsloth = True
            print("✨ Using Unsloth for CUDA optimization")
        except ImportError:
            print("⚠️ Unsloth not found. Falling back to standard PEFT.")

    if use_unsloth:
        model, tokenizer = FastLanguageModel.from_pretrained(
            model_name      = BASE_MODEL,
            max_seq_length  = MAX_SEQ_LEN,
            dtype           = None, # auto
            load_in_4bit    = True,
        )
        model = FastLanguageModel.get_peft_model(
            model,
            r = LORA_RANK,
            target_modules = TARGET_MODULES,
            lora_alpha = LORA_ALPHA,
            lora_dropout = LORA_DROPOUT,
            bias = "none",
            use_gradient_checkpointing = "unsloth",
            random_state = 42,
        )
    else:
        from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
        from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training

        tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL_HF)
        tokenizer.pad_token = tokenizer.eos_token

        # Quantization config (only for CUDA/MPS fallback where bitsandbytes is available)
        bnb_config = None
        if device == "cuda":
            bnb_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_compute_dtype=torch.float16,
                bnb_4bit_use_double_quant=True,
            )
        
        model = AutoModelForCausalLM.from_pretrained(
            BASE_MODEL_HF,
            quantization_config=bnb_config,
            device_map="auto" if device != "cpu" else None,
            torch_dtype=torch.float16 if device != "cpu" else torch.float32,
        )

        model = prepare_model_for_kbit_training(model)
        peft_config = LoraConfig(
            r=LORA_RANK,
            lora_alpha=LORA_ALPHA,
            target_modules=TARGET_MODULES,
            lora_dropout=LORA_DROPOUT,
            bias="none",
            task_type="CAUSAL_LM",
        )
        model = get_peft_model(model, peft_config)

    model.print_trainable_parameters()

    # ── 3. Dataset ────────────────────────────────────────────────────── #
    from datasets import Dataset

    def load_ds(path):
        records = load_jsonl(path)
        formatted = [format_chatml(r, tokenizer) for r in records]
        return Dataset.from_list(formatted)

    print(f"\nLoading datasets...")
    train_ds = load_ds(args.train_file)
    eval_ds  = load_ds(args.eval_file)  if os.path.exists(args.eval_file) else None
    print(f"  Train : {len(train_ds)} samples")
    if eval_ds:
        print(f"  Eval  : {len(eval_ds)} samples")

    # ── 4. Training arguments ─────────────────────────────────────────── #
    from trl import SFTTrainer
    from transformers import TrainingArguments

    training_args = TrainingArguments(
        output_dir             = args.output_dir,
        num_train_epochs       = args.epochs,
        per_device_train_batch_size  = args.batch_size,
        gradient_accumulation_steps  = args.grad_accum,
        learning_rate          = args.lr,
        warmup_ratio           = args.warmup_ratio,
        lr_scheduler_type      = "cosine",
        fp16                   = device == "cuda" and not torch.cuda.is_bf16_supported(),
        bf16                   = device == "cuda" and torch.cuda.is_bf16_supported(),
        optim                  = "adamw_8bit" if device == "cuda" else "adamw_torch",
        weight_decay           = 0.01,
        logging_steps          = 10,
        evaluation_strategy    = "epoch" if eval_ds else "no",
        save_strategy          = "epoch",
        save_total_limit       = 2,
        load_best_model_at_end = True if eval_ds else False,
        metric_for_best_model  = "eval_loss" if eval_ds else None,
        report_to              = "none",
        seed                   = 42,
    )

    # ── 5. SFT Trainer ────────────────────────────────────────────────── #
    trainer = SFTTrainer(
        model            = model,
        tokenizer        = tokenizer,
        train_dataset    = train_ds,
        eval_dataset     = eval_ds,
        dataset_text_field = "text",
        max_seq_length   = MAX_SEQ_LEN,
        dataset_num_proc = 2,
        packing          = False,   # set True to pack short sequences (faster)
        args             = training_args,
    )

    # ── 6. Train ─────────────────────────────────────────────────────── #
    print(f"\n🚀 Starting fine-tuning...\n")
    trainer_stats = trainer.train()

    print(f"\n✅ Training complete!")
    print(f"   Elapsed: {trainer_stats.metrics['train_runtime']:.0f}s")
    print(f"   Samples/sec: {trainer_stats.metrics['train_samples_per_second']:.2f}")

    # ── 7. Save LoRA adapter ─────────────────────────────────────────── #
    Path(args.output_dir).mkdir(parents=True, exist_ok=True)
    model.save_pretrained(args.output_dir)
    tokenizer.save_pretrained(args.output_dir)
    print(f"\n💾 LoRA adapter saved → {args.output_dir}/")

    # ── 8. GGUF export (optional — for Ollama) ───────────────────────── #
    if args.save_gguf:
        if not use_unsloth:
            print("\n⚠️ GGUF export via script is only supported with Unsloth.")
            print("   Please use llama.cpp manually to convert the LoRA adapter.")
        else:
            gguf_path = os.path.join(args.output_dir, "gguf")
            print(f"\n📦 Exporting GGUF ({args.gguf_quant}) → {gguf_path}/")
            model.save_pretrained_gguf(
                gguf_path,
                tokenizer,
                quantization_method = args.gguf_quant,
            )
            print(f"\n✅ GGUF exported! Load into Ollama:")
            print(f"   1.  Create a Modelfile:")
            print(f"       FROM {gguf_path}/model-{args.gguf_quant.upper()}.gguf")
            print(f"   2.  ollama create protofolio-chairman -f Modelfile")
            print(f"   3.  Set OLLAMA_MODEL=protofolio-chairman in your .env")

    print(f"\n🎉 All done. Next step: run finetune/push_to_hub.py if you want to upload to HuggingFace Hub.")


if __name__ == "__main__":
    main()
