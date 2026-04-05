# 🚀 Protofolio Fine-Tuning Guide (Google Colab)

This guide explains how to fine-tune **Llama 3.1 8B** to act as your **Chairman SME** using the scripts generated in this repository.

## Prerequisites
1. **Google Colab** (T4 GPU free tier is sufficient).
2. **Hugging Face Token** (with Write access).
3. **Google API Key** (for synthetic data generation via Gemini).

---

## Step 1: Upload Scripts to Colab
1. Open a new [Google Colab Notebook](https://colab.research.google.com/).
2. Create a folder named `finetune` in the Colab file explorer.
3. Upload the following files from your local `finetune/` directory to the Colab `finetune/` folder:
   - `requirements_finetune.txt`
   - `generate_training_data.py`
   - `train_lora.py`
   - `push_to_hub.py`
   - `eval_finetuned.py`

---

## Step 2: Install Dependencies
Run this in a Colab cell:
```python
!pip install -r finetune/requirements_finetune.txt
```

---

## Step 3: Generate Training Data
Export your Gemini API Key and run the generator. This uses Gemini as an "oracle" to create high-quality portfolio blueprints.
```python
import os
os.environ["GOOGLE_API_KEY"] = "your_gemini_api_key_here"

!python finetune/generate_training_data.py --num_samples 300
```
*This will create `finetune/data/train.jsonl` and `finetune/data/eval.jsonl`.*

---

## Step 4: Run Fine-Tuning (QLoRA)
This script uses **Unsloth** for extremely fast training on a single T4 GPU.
```python
!python finetune/train_lora.py \
    --train_file finetune/data/train.jsonl \
    --eval_file  finetune/data/eval.jsonl  \
    --output_dir finetune/lora_adapter      \
    --epochs 3 \
    --save_gguf \
    --gguf_quant q4_k_m
```
*Wait for ~2 hours. It will save the LoRA weights and a GGUF file for Ollama.*

---

## Step 5: Push to Hugging Face
```python
os.environ["HUGGINGFACE_TOKEN"] = "your_hf_token_here"

!python finetune/push_to_hub.py \
    --adapter_dir finetune/lora_adapter \
    --repo_id     "your-username/protofolio-chairman-lora"
```

---

## Step 6: Deploy Locally via Ollama
Once training is done and you have the GGUF file (or download it from your HF repo):

1. **Install Ollama**: `brew install ollama` (if on Mac).
2. **Create Modelfile**: 
   ```bash
   FROM ./finetune/lora_adapter/gguf/model-Q4_K_M.gguf
   SYSTEM "You are Sophia, the unified Council Chairman and Subject Matter Expert (SME)..."
   ```
3. **Create Model**:
   ```bash
   ollama create protofolio-chairman -f Modelfile
   ```
4. **Update .env**:
   ```env
   OLLAMA_MODEL=protofolio-chairman
   OLLAMA_HOST=http://localhost:11434
   ```

---

## Step 7: Verify
Run the evaluation script to see if the fine-tuned model actually follows the JSON schema better than the base model:
```python
!python finetune/eval_finetuned.py --ollama_model protofolio-chairman
```
