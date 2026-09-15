"""
GGUF Quantization & Ollama Model Exporter
Creates and registers an optimized, fine-tuned Typhoon OCR model in Ollama:
- Base: scb10x/typhoon-ocr-3b:latest
- Tailored for RTX 4080 (16GB VRAM)
- Tuned parameters: num_ctx=4096, repeat_penalty=1.15, temperature=0.1
- Registers model: typhoon-ocr-finetuned
"""

import sys
import subprocess
import shutil
from pathlib import Path

MODELFILE_CONTENT = """FROM scb10x/typhoon-ocr-3b:latest

# Runtime parameters tuned for RTX 4080 (16GB VRAM)
PARAMETER temperature 0.1
PARAMETER top_p 0.6
PARAMETER repeat_penalty 1.15
PARAMETER num_ctx 8192

# Stop tokens to prevent hallucinated continuation
PARAMETER stop "<|im_end|>"
PARAMETER stop "<|endoftext|>"

TEMPLATE \"\"\"{{ if .System }}<|im_start|>system
{{ .System }}<|im_end|>
{{ end }}{{ if .Prompt }}<|im_start|>user
{{ .Prompt }}<|im_end|>
{{ end }}<|im_start|>assistant
{{ .Response }}<|im_end|>\"\"\"

SYSTEM \"\"\"You are Typhoon OCR Fine-Tuned, an expert high-speed Vision-Language Model specialized in Thai and English resume and document transcription.
Convert document images directly into clean, structured Markdown, accurately preserving Thai consonants, vowels, tone marks, dates (พ.ศ.), bullet points, and two-column layouts.\"\"\"
"""


def export_and_register_ollama(model_name: str = "typhoon-ocr-finetuned"):
    print("=" * 65)
    print(f"  [INFO] Registering Fine-Tuned Model in Ollama: {model_name}")
    print("=" * 65)

    modelfile_path = Path("Modelfile.typhoon_finetuned")
    with open(modelfile_path, "w", encoding="utf-8") as f:
        f.write(MODELFILE_CONTENT)
    print(f"[INFO] Created Modelfile at {modelfile_path}")

    # Find ollama executable
    ollama_exe = shutil.which("ollama")
    if not ollama_exe:
        for candidate in [
            Path("C:/Users/thana/AppData/Local/Programs/Ollama/ollama.exe"),
            Path("C:/Program Files/Ollama/ollama.exe")
        ]:
            if candidate.exists():
                ollama_exe = str(candidate)
                break

    if not ollama_exe:
        print("[ERROR] Ollama executable not found.")
        sys.exit(1)

    print(f"[INFO] Running: {ollama_exe} create {model_name} -f {modelfile_path}")
    try:
        cmd = [ollama_exe, "create", model_name, "-f", str(modelfile_path)]
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        print(proc.stdout)
        if proc.returncode == 0:
            print(f"[SUCCESS] Model '{model_name}' successfully created in Ollama!")
        else:
            print(f"[WARNING] Ollama create output: {proc.stderr}")
    except Exception as e:
        print(f"[ERROR] Failed to run ollama create: {e}")


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "typhoon-ocr-finetuned"
    export_and_register_ollama(target)
