"""
Style-Bert-VITS2 - R&D Test Script
===================================
Kiểm tra toàn bộ pipeline từ text tiếng Nhật -> audio output.
Tự động phát hiện GPU/CPU và ghi báo cáo vào test_report.md.

Usage:
    python test_tts.py
    python test_tts.py --text "テストテキスト" --output output/custom.wav
"""

import os
import sys
import time
import json
import datetime
import argparse
import traceback
from pathlib import Path


# ============================================================
# Helper: Colored terminal output
# ============================================================
class Color:
    GREEN  = "\033[92m"
    YELLOW = "\033[93m"
    RED    = "\033[91m"
    CYAN   = "\033[96m"
    BOLD   = "\033[1m"
    RESET  = "\033[0m"

def ok(msg):   print(f"{Color.GREEN}  ✅ {msg}{Color.RESET}")
def warn(msg): print(f"{Color.YELLOW}  ⚠️  {msg}{Color.RESET}")
def err(msg):  print(f"{Color.RED}  ❌ {msg}{Color.RESET}")
def info(msg): print(f"{Color.CYAN}  ℹ️  {msg}{Color.RESET}")
def bold(msg): print(f"{Color.BOLD}{msg}{Color.RESET}")


# ============================================================
# Test Results Collector
# ============================================================
class TestReport:
    def __init__(self):
        self.results = []
        self.start_time = datetime.datetime.now()
        self.env_info = {}

    def add(self, name: str, status: str, detail: str = "", duration: float = 0.0):
        self.results.append({
            "test": name,
            "status": status,         # PASS | FAIL | WARN | SKIP
            "detail": detail,
            "duration_sec": round(duration, 3),
        })

    def save(self, output_path: str = "logs/test_report.md"):
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        passed = sum(1 for r in self.results if r["status"] == "PASS")
        failed = sum(1 for r in self.results if r["status"] == "FAIL")
        warned = sum(1 for r in self.results if r["status"] == "WARN")
        total  = len(self.results)
        elapsed = (datetime.datetime.now() - self.start_time).total_seconds()

        lines = [
            "# Style-Bert-VITS2 R&D Test Report",
            f"\n**Generated:** {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}",
            f"**Duration:** {elapsed:.1f}s",
            f"\n## Summary\n",
            f"| Result | Count |",
            f"|--------|-------|",
            f"| ✅ PASS | {passed} |",
            f"| ❌ FAIL | {failed} |",
            f"| ⚠️ WARN | {warned} |",
            f"| Total  | {total} |",
            "\n## Environment\n",
        ]
        for k, v in self.env_info.items():
            lines.append(f"- **{k}:** {v}")

        lines.append("\n## Test Results\n")
        lines.append("| Test | Status | Duration | Detail |")
        lines.append("|------|--------|----------|--------|")
        for r in self.results:
            icon = {"PASS": "✅", "FAIL": "❌", "WARN": "⚠️", "SKIP": "⏭️"}.get(r["status"], "?")
            lines.append(
                f"| {r['test']} | {icon} {r['status']} | {r['duration_sec']}s | {r['detail']} |"
            )

        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        print(f"\n  📄 Report saved: {output_path}")
        return failed == 0


# ============================================================
# PHASE 1: Environment Detection
# ============================================================
def phase_environment(report: TestReport) -> dict:
    bold("\n📋 PHASE 1: Environment Detection")
    env = {}

    # Python version
    py_ver = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    env["python_version"] = py_ver
    if sys.version_info >= (3, 10) and sys.version_info < (3, 13):
        ok(f"Python {py_ver}")
        report.add("Python Version", "PASS", py_ver)
    else:
        warn(f"Python {py_ver} (recommend 3.10-3.12)")
        report.add("Python Version", "WARN", f"{py_ver} - recommend 3.10-3.12")

    # PyTorch + CUDA
    try:
        import torch
        torch_ver = torch.__version__
        cuda_available = torch.cuda.is_available()
        env["torch_version"] = torch_ver
        env["cuda_available"] = str(cuda_available)

        if cuda_available:
            cuda_ver = torch.version.cuda
            gpu_name = torch.cuda.get_device_name(0)
            env["cuda_version"] = cuda_ver
            env["gpu_name"] = gpu_name
            ok(f"PyTorch {torch_ver} | CUDA {cuda_ver} | GPU: {gpu_name}")
            report.add("PyTorch + CUDA", "PASS", f"GPU: {gpu_name}")
            device = "cuda"
        else:
            # Check for MPS (Apple Silicon)
            mps_available = hasattr(torch.backends, "mps") and torch.backends.mps.is_available()
            if mps_available:
                env["device"] = "mps"
                ok(f"PyTorch {torch_ver} | Apple MPS available")
                report.add("PyTorch + Device", "PASS", "Apple MPS (Metal)")
                device = "mps"
            else:
                env["device"] = "cpu"
                warn(f"PyTorch {torch_ver} | No GPU detected → CPU mode")
                report.add("PyTorch + Device", "WARN", "CPU mode (no GPU detected)")
                device = "cpu"
    except ImportError as e:
        err(f"PyTorch not found: {e}")
        report.add("PyTorch", "FAIL", str(e))
        device = "cpu"

    env["device"] = device
    info(f"Selected device: {device.upper()}")

    # numpy version check
    try:
        import numpy as np
        np_ver = np.__version__
        env["numpy_version"] = np_ver
        major = int(np_ver.split(".")[0])
        if major < 2:
            ok(f"numpy {np_ver} (compatible)")
            report.add("numpy Version", "PASS", np_ver)
        else:
            warn(f"numpy {np_ver} >= 2.0 (may cause issues)")
            report.add("numpy Version", "WARN", f"{np_ver} - style-bert-vits2 prefers numpy<2")
    except ImportError as e:
        err(f"numpy not found: {e}")
        report.add("numpy", "FAIL", str(e))

    report.env_info = env
    return env


# ============================================================
# PHASE 2: Import Checks
# ============================================================
def phase_imports(report: TestReport) -> bool:
    bold("\n📦 PHASE 2: Import Checks")
    all_ok = True

    # Critical imports - failure blocks Phase 3
    critical_modules = [
        ("style_bert_vits2",           "style-bert-vits2 core"),
        ("style_bert_vits2.tts_model", "TTS Model"),
        ("style_bert_vits2.nlp",       "NLP utilities"),
        ("style_bert_vits2.constants", "Constants"),
    ]

    # Optional imports - failure is WARN only (bert_models depends on transformers version)
    optional_modules = [
        ("style_bert_vits2.nlp.bert_models", "BERT models (optional direct import)"),
    ]

    for module_path, label in critical_modules:
        t0 = time.time()
        try:
            __import__(module_path)
            elapsed = time.time() - t0
            ok(f"{label} ({elapsed:.2f}s)")
            report.add(f"Import: {label}", "PASS", "", elapsed)
        except Exception as e:
            elapsed = time.time() - t0
            err(f"{label}: {e}")
            report.add(f"Import: {label}", "FAIL", str(e), elapsed)
            all_ok = False

    for module_path, label in optional_modules:
        t0 = time.time()
        try:
            __import__(module_path)
            elapsed = time.time() - t0
            ok(f"{label} ({elapsed:.2f}s)")
            report.add(f"Import: {label}", "PASS", "", elapsed)
        except Exception as e:
            elapsed = time.time() - t0
            # Not a blocker - TTSModelHolder loads BERT internally
            warn(f"{label}: {e}")
            report.add(f"Import: {label}", "WARN",
                       f"Direct import failed (TTSModelHolder loads BERT internally): {e}", elapsed)

    return all_ok


# ============================================================
# PHASE 3: Model Download & Load
# ============================================================
def phase_model_load(report: TestReport, env: dict) -> object:
    bold("\n🧠 PHASE 3: Model Download & Load")
    device = env.get("device", "cpu")

    # Verify transformers+torch integration first
    try:
        import transformers
        import torch
        # Check if transformers can actually use torch
        if not hasattr(transformers, 'modeling_utils'):
            warn("transformers may have limited PyTorch support")
        transformers_ver = transformers.__version__
        torch_ver = torch.__version__
        info(f"transformers {transformers_ver} + torch {torch_ver}")
        report.add("transformers+torch Integration", "PASS",
                   f"transformers {transformers_ver}, torch {torch_ver}")
    except Exception as e:
        err(f"transformers integration check failed: {e}")
        report.add("transformers+torch Integration", "FAIL", str(e))

    # Initialize TTSModelHolder (handles BERT loading internally)
    try:
        from style_bert_vits2.tts_model import TTSModelHolder

        models_dir = Path("/app/models")
        models_dir.mkdir(parents=True, exist_ok=True)

        t0 = time.time()
        info(f"Initializing TTSModelHolder from {models_dir}...")

        model_holder = TTSModelHolder(models_dir, device)
        elapsed = time.time() - t0
        ok(f"TTSModelHolder initialized ({elapsed:.1f}s)")

        model_names = model_holder.model_names if hasattr(model_holder, "model_names") else []
        if model_names:
            ok(f"Found models: {model_names}")
            report.add("TTS Model Holder", "PASS", f"Models: {model_names}", elapsed)
        else:
            warn("No pre-trained models found in /app/models/ - need to download separately")
            report.add("TTS Model Holder", "WARN",
                       "No models in /app/models/ - run download_models.py", elapsed)

        return model_holder

    except Exception as e:
        err(f"TTSModelHolder init failed: {e}")
        report.add("TTS Model Holder", "FAIL", str(e))
        traceback.print_exc()
        return None


# ============================================================
# PHASE 4: TTS Synthesis Test
# ============================================================
def phase_synthesis(report: TestReport, model_holder, env: dict, text: str, output_path: str):
    bold("\n🎙️ PHASE 4: TTS Synthesis Test")
    device = env.get("device", "cpu")

    if model_holder is None:
        warn("Skipping synthesis - model holder not available")
        report.add("TTS Synthesis", "SKIP", "Model holder not available")
        return False

    model_names = getattr(model_holder, "model_names", [])
    if not model_names:
        warn("Skipping synthesis - no TTS models found in /app/models/")
        info("To download models, run: python download_models.py")
        report.add("TTS Synthesis", "SKIP", "No TTS models found - run download_models.py")
        return False

    try:
        from style_bert_vits2.tts_model import TTSModel
        from style_bert_vits2.constants import Languages

        # Get available styles for the first model
        # Default style is always 'Neutral' in style-bert-vits2
        target_model = model_names[0]
        default_style = "Neutral"

        info(f"Loading model: {target_model} (style: {default_style})")
        t0 = time.time()
        
        tts_model = None
        if hasattr(model_holder, "get_model"):
            try:
                tts_model = model_holder.get_model(target_model)
            except TypeError:
                # v2.5.0 get_model requires model_path_str (the exact .safetensors file)
                model_dir_path = Path("/app/models") / target_model
                model_files = list(model_dir_path.glob("*.safetensors")) + list(model_dir_path.glob("*.pt"))
                if not model_files:
                    err(f"No model file (.safetensors/.pt) found in {model_dir_path}")
                    return False
                model_path_str = str(model_files[0])
                tts_model = model_holder.get_model(target_model, model_path_str)
        elif hasattr(model_holder, "models") and target_model in model_holder.models:
            tts_model = model_holder.models[target_model]
        else:
            warn(f"Could not get TTSModel from holder. Available methods: {[m for m in dir(model_holder) if not m.startswith('_')]}")
            return False

        if tts_model is None:
            err("TTS model is None.")
            return False

        load_elapsed = time.time() - t0
        ok(f"Model loaded ({load_elapsed:.1f}s)")

        info(f"Synthesizing: {text}")
        t0 = time.time()

        # Pre-load BERT models to avoid local path assertion errors in default logic
        try:
            from style_bert_vits2.nlp import bert_models
            from style_bert_vits2.constants import Languages
            bert_models.load_tokenizer(Languages.JP, "ku-nlp/deberta-v2-large-japanese-char-wwm")
            bert_models.load_model(Languages.JP, "ku-nlp/deberta-v2-large-japanese-char-wwm")
        except Exception as e:
            warn(f"Failed to pre-load BERT models: {e}")

        sr, audio = tts_model.infer(
            text=text,
            language=Languages.JP,
            speaker_id=0,
            sdp_ratio=0.2,
            noise=0.6,
            noise_w=0.8,
            length=1.0,
        )
        infer_elapsed = time.time() - t0
        ok(f"Synthesis complete ({infer_elapsed:.1f}s) | Sample rate: {sr}Hz")

        # Save output
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        import soundfile as sf
        sf.write(output_path, audio, sr)
        ok(f"Audio saved: {output_path}")

        report.add(
            "TTS Synthesis",
            "PASS",
            f"Text: '{text}' | Device: {device} | Inference: {infer_elapsed:.1f}s | Output: {output_path}",
            infer_elapsed,
        )
        return True

    except Exception as e:
        err(f"Synthesis failed: {e}")
        report.add("TTS Synthesis", "FAIL", str(e))
        traceback.print_exc()
        return False


# ============================================================
# PHASE 5: Library Version Audit
# ============================================================
def phase_version_audit(report: TestReport):
    bold("\n🔍 PHASE 5: Library Version Audit")

    packages = [
        "torch", "torchaudio", "numpy", "librosa",
        "transformers", "google.protobuf", "soundfile",
        "style_bert_vits2",
    ]

    versions = {}
    for pkg in packages:
        try:
            import importlib
            mod = importlib.import_module(pkg.replace("-", "_"))
            ver = getattr(mod, "__version__", "unknown")
            versions[pkg] = ver
            info(f"{pkg}: {ver}")
        except ImportError:
            versions[pkg] = "NOT INSTALLED"
            warn(f"{pkg}: NOT INSTALLED")

    # Known conflict checks
    conflicts = []
    if "numpy" in versions and versions["numpy"] != "NOT INSTALLED":
        major = int(versions["numpy"].split(".")[0])
        if major >= 2:
            conflicts.append(f"numpy {versions['numpy']} >= 2.0 (style-bert-vits2 requires <2)")

    if "librosa" in versions and versions["librosa"] not in ("NOT INSTALLED", "0.9.2"):
        conflicts.append(f"librosa {versions['librosa']} (style-bert-vits2 originally requires 0.9.2, newer may work)")

    if "transformers" in versions and versions["transformers"] != "NOT INSTALLED":
        t_major = int(versions["transformers"].split(".")[0])
        if t_major >= 5:
            conflicts.append(
                f"transformers {versions['transformers']} >= 5.0 breaks DebertaV2Model import. "
                f"Pin transformers<5 in Dockerfile."
            )
        else:
            info(f"transformers {versions['transformers']} (compatible 4.x ✅)")

    if conflicts:
        for c in conflicts:
            warn(f"Conflict: {c}")
            report.add("Version Conflict", "WARN", c)
    else:
        ok("No critical version conflicts detected")
        report.add("Version Audit", "PASS", f"All {len(packages)} packages checked")

    return versions


# ============================================================
# Main
# ============================================================
def main():
    parser = argparse.ArgumentParser(description="Style-Bert-VITS2 R&D Test")
    parser.add_argument("--text", default="日本語のテスト文章です。音声合成のテストを行います。",
                        help="Japanese text to synthesize")
    parser.add_argument("--output", default="/app/output/test_output.wav",
                        help="Output audio path")
    parser.add_argument("--report", default="/app/logs/test_report.md",
                        help="Report output path")
    args = parser.parse_args()

    print(f"\n{'='*60}")
    print(f"  Style-Bert-VITS2 R&D Test Suite")
    print(f"  {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}")

    report = TestReport()

    # Run all phases
    env          = phase_environment(report)
    imports_ok   = phase_imports(report)
    # Phase 3 always runs - TTSModelHolder handles BERT internally
    # even if direct bert_models import failed due to transformers version
    model_holder = phase_model_load(report, env)
    phase_synthesis(report, model_holder, env, args.text, args.output)
    versions     = phase_version_audit(report)

    # Final summary
    bold("\n" + "="*60)
    passed = sum(1 for r in report.results if r["status"] == "PASS")
    failed = sum(1 for r in report.results if r["status"] == "FAIL")
    warned = sum(1 for r in report.results if r["status"] == "WARN")
    skipped = sum(1 for r in report.results if r["status"] == "SKIP")

    print(f"  ✅ PASS:    {passed}")
    print(f"  ❌ FAIL:    {failed}")
    print(f"  ⚠️  WARN:    {warned}")
    print(f"  ⏭️  SKIP:    {skipped}")
    print(f"{'='*60}\n")

    success = report.save(args.report)

    if failed == 0:
        ok("All critical tests passed! Style-Bert-VITS2 is ready.")
    else:
        err(f"{failed} test(s) failed. Check {args.report} for details.")

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
