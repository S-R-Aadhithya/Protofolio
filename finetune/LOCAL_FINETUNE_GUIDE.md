# 🚀 Local Fine-Tuning Guide (24GB VRAM)

This guide is for running the Protofolio fine-tuning pipeline on a local machine (NVIDIA GPU or Apple Silicon).

## 🛠️ Step 1: Environment Setup

Clone the repository and install dependencies.

```bash
# 1. Create a virtual environment
python -m venv venv
source venv/bin/activate  # Mac/Linux
# venv\Scripts\activate  # Windows

# 2. Install requirements
# Your requirements_finetune.txt is now hardware-agnostic.
pip install -r finetune/requirements_finetune.txt
```

> [!TIP]
> **NVIDIA Users**: The requirements will automatically attempt to install `unsloth` for 4x faster training. If it fails, the script will automatically fallback to standard Hugging Face PEFT.

---

## 🧬 Step 2: Generate Training Data

Before training, you need to generate the synthetic dataset. This requires a **Gemini API Key**.

1. Create/Edit the `.env` file in the root:
   ```env
   GOOGLE_API_KEY=your_api_key_here
   ```
2. Run the generator:
   ```bash
   python finetune/generate_training_data.py --num_samples 300
   ```
   *This will create `finetune/data/train.jsonl` and `finetune/data/eval.jsonl`.*

---

## 🏎️ Step 3: Run Fine-Tuning (MPS/CUDA)

The script `train_lora.py` has been updated to automatically detect your hardware.

```bash
python finetune/train_lora.py \
    --train_file finetune/data/train.jsonl \
    --eval_file  finetune/data/eval.jsonl  \
    --output_dir finetune/lora_adapter      \
    --epochs 3 \
    --save_gguf \
    --gguf_quant q4_k_m
```

### What happens under the hood:
- **On NVIDIA (CUDA)**: Uses `unsloth` for extremely fast QLoRA training.
- **On Mac (MPS)**: Uses standard `peft` and `transformers` fallback.
- **24GB VRAM**: With 24GB, this will run comfortably and fast. Expected time for 300 samples: **~30-45 minutes** on an RTX 3090/4090.

---

## 📦 Step 4: Export to Ollama

If you used `--save_gguf`, you will find a GGUF file in `finetune/lora_adapter/gguf/`.

1. **Install Ollama**: [ollama.com](https://ollama.com)
2. **Create a Modelfile**:
   ```bash
   # Create a file named 'Modelfile'
   FROM ./finetune/lora_adapter/gguf/model-Q4_K_M.gguf
   SYSTEM "You are Sophia, the unified Council Chairman and Subject Matter Expert (SME)..."
   ```
3. **Build and Run**:
   ```bash
   ollama create protofolio-chairman -f Modelfile
   ollama run protofolio-chairman
   ```

---

## ✅ Verification
Run the evaluation script to verify the model:
```bash
python finetune/eval_finetuned.py --ollama_model protofolio-chairman
```
