"""Run export_scratch_artifacts(...) in the trusted training notebook after training.

Uses the BEST checkpoint file, not the last epoch's in-memory weights.
Does not train or download a model. Output directory must be new/empty.
"""
from __future__ import annotations
import hashlib
import importlib.metadata
import json
from pathlib import Path
import platform


def export_scratch_artifacts(checkpoint_path, tokenizer, seq2seq_config, output_dir,
                             generation_config=None, *, min_new_tokens=0):
    import torch
    from transformers import GenerationConfig

    output = Path(output_dir)
    if output.exists() and any(output.iterdir()):
        raise ValueError("Use a new/empty output directory; do not overwrite an existing bundle")
    if type(min_new_tokens) is not int or min_new_tokens < 0:
        raise ValueError("min_new_tokens must be a nonnegative integer")
    checkpoint = torch.load(checkpoint_path, map_location="cpu", weights_only=True)
    for key in ("model_state_dict", "config", "seq2seq_model_name", "num_visual_tokens"):
        if key not in checkpoint:
            raise ValueError(f"Missing checkpoint key: {key}")
    if checkpoint["seq2seq_model_name"] != "VietAI/vit5-base" or seq2seq_config.model_type != "t5":
        raise ValueError("This exporter is for ResNet101 + VietAI/vit5-base VQA")
    # Keep only inference settings, stripping Kaggle/data paths and unrelated state.
    keys = ("IMG_SIZE", "MAX_QUESTION_LEN", "GEN_MAX_LENGTH", "GEN_NUM_BEAMS",
            "ANSWER_MARKER", "USE_KB_CONTEXT", "USE_RATIONALE",
            "NUM_VISUAL_TOKENS", "SEQ2SEQ_MODEL_NAME")
    safe_config = {key: checkpoint["config"][key] for key in keys if key in checkpoint["config"]}
    cleaned = {key: checkpoint[key] for key in
               ("model_state_dict", "seq2seq_model_name", "num_visual_tokens")}
    cleaned["config"] = safe_config
    output.mkdir(parents=True, exist_ok=True)
    assets = output / "vit5"
    assets.mkdir()
    tokenizer.save_pretrained(assets)
    seq2seq_config.save_pretrained(assets)
    if generation_config is None:
        generation_config = GenerationConfig.from_model_config(seq2seq_config)
    generation_config.save_pretrained(assets)
    torch.save(cleaned, output / "best_vqa_model.pt")

    hashes = {}
    for path in sorted(output.rglob("*")):
        if path.is_file():
            digest = hashlib.sha256()
            with path.open("rb") as stream:
                for block in iter(lambda: stream.read(1024 * 1024), b""):
                    digest.update(block)
            hashes[path.relative_to(output).as_posix()] = digest.hexdigest()
    packages = {}
    for name in ("torch", "torchvision", "transformers", "tokenizers", "sentencepiece", "Pillow"):
        try:
            packages[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            packages[name] = None
    manifest = {
        "format_version": 1, "architecture": "resnet101-vit5-vqa",
        "input_mode": "question_only", "min_new_tokens": min_new_tokens,
        "sha256": hashes, "export_environment": {"python": platform.python_version(), **packages},
        "notes": "Question-only matches notebook cell 48; training may have used KB context. "
                 "min_new_tokens=0 matches notebook; original scratch_model.py used 5.",
    }
    (output / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return output
