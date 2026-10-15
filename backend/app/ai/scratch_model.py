"""Adapter VQA ResNet101 + ViT5; AI imports are deferred until load().

Manager must serialize load/predict/unload across ALL adapters. Caller owns the
RGB image. No HTTP, image persistence, model download, or background workers here.
"""
from __future__ import annotations

import gc
import hashlib
import json
import logging
import math
from pathlib import Path
from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from PIL import Image

from app.ai.base import BaseVIVQAModel
from app.config import get_settings

_LOG = logging.getLogger(__name__)
_BACKEND_ROOT = Path(__file__).resolve().parents[2]
MEAN = (0.485, 0.456, 0.406)
STD = (0.229, 0.224, 0.225)


def _app_error(status_code: int, code: str, message: str) -> Exception:
    # Keyword arguments match app.errors.AppError in this repository.
    from app.errors import AppError
    return AppError(status_code=status_code, code=code, message=message)


def extract_answer(raw_text: str, marker: str = "Trả lời:") -> str:
    """Match notebook extract_final_answer; never substitute a missing answer."""
    text = raw_text.strip()
    marker = marker.strip()
    if not marker:
        raise ValueError("ANSWER_MARKER must not be blank")
    if marker in text:
        text = text.split(marker, 1)[1].strip()
    if not text:
        raise ValueError("Model generated an empty final answer")
    return text


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _local_file(root: Path, relative: str) -> Path:
    if not isinstance(relative, str) or not relative or Path(relative).is_absolute():
        raise ValueError("Artifact path must be relative")
    path = (root / relative).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError("Artifact path is outside model directory")
    if not path.is_file():
        raise FileNotFoundError(f"Missing artifact: {relative}")
    return path


def read_manifest(root: Path) -> dict:
    """Read/check local files without importing AI or loading weights.

    File presence is a preflight only, not proof the model can be loaded.
    Full checksum verification is done during load, not every GET /models.
    """
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    if (manifest.get("format_version") != 1
            or manifest.get("architecture") != "resnet101-vit5-vqa"
            or manifest.get("input_mode") != "question_only"):
        raise ValueError("Unsupported scratch artifact format/architecture/input mode")
    hashes = manifest.get("sha256")
    if not isinstance(hashes, dict) or not hashes:
        raise ValueError("Missing artifact checksums")
    required = {
        "best_vqa_model.pt", "vit5/config.json", "vit5/generation_config.json",
        "vit5/tokenizer_config.json", "vit5/special_tokens_map.json", "vit5/spiece.model",
    }
    if not required.issubset(hashes):
        raise ValueError("Manifest does not include all required files")
    for name, digest in hashes.items():
        _local_file(root, name)
        if (not isinstance(digest, str) or len(digest) != 64
                or any(c not in "0123456789abcdef" for c in digest)):
            raise ValueError("Invalid SHA256 digest")
    minimum = manifest.get("min_new_tokens")
    if type(minimum) is not int or minimum < 0:
        raise ValueError("Invalid min_new_tokens")
    return manifest


def _read_settings(checkpoint: dict) -> dict:
    if not isinstance(checkpoint, dict) or not isinstance(checkpoint.get("model_state_dict"), dict):
        raise ValueError("Expected full notebook checkpoint, not bare state_dict or adapter")
    if checkpoint.get("seq2seq_model_name") != "VietAI/vit5-base":
        raise ValueError("Expected VietAI/vit5-base checkpoint")
    config = checkpoint.get("config")
    if not isinstance(config, dict):
        raise ValueError("Checkpoint config is required")
    for key in ("IMG_SIZE", "MAX_QUESTION_LEN", "GEN_MAX_LENGTH", "GEN_NUM_BEAMS"):
        if type(config.get(key)) is not int or config[key] <= 0:
            raise ValueError(f"Invalid or missing {key}")
    if config["GEN_MAX_LENGTH"] < 2:
        raise ValueError("GEN_MAX_LENGTH must be >= 2")
    tokens = checkpoint.get("num_visual_tokens")
    if type(tokens) is not int or tokens <= 0 or math.isqrt(tokens) ** 2 != tokens:
        raise ValueError("num_visual_tokens must be a positive square")
    if config.get("NUM_VISUAL_TOKENS", tokens) != tokens:
        raise ValueError("Conflicting visual token settings")
    if config.get("SEQ2SEQ_MODEL_NAME", "VietAI/vit5-base") != "VietAI/vit5-base":
        raise ValueError("Conflicting seq2seq settings")
    if not isinstance(config.get("ANSWER_MARKER"), str) or not config["ANSWER_MARKER"].strip():
        raise ValueError("ANSWER_MARKER is required")
    if type(config.get("USE_KB_CONTEXT")) is not bool:
        raise ValueError("USE_KB_CONTEXT must be recorded in checkpoint")
    return dict(config)


def _build_model(seq2seq_config, num_visual_tokens: int):
    """Parameter names/layout match notebook cell 29 and original scratch_model.py."""
    import torch
    import torch.nn as nn
    from torchvision.models import resnet101
    from transformers import AutoModelForSeq2SeqLM

    class ImageEncoder(nn.Module):
        def __init__(self, d_model, num_tokens):
            super().__init__()
            backbone = resnet101(weights=None)  # all weights come from checkpoint
            self.feat_dim = backbone.fc.in_features
            self.backbone = nn.Sequential(*list(backbone.children())[:-2])
            side = math.isqrt(num_tokens)
            self.pool = nn.AdaptiveAvgPool2d((side, side))
            self.projector = nn.Sequential(
                nn.Linear(self.feat_dim, d_model), nn.GELU(),
                nn.LayerNorm(d_model), nn.Dropout(0.1),
            )

        def forward(self, images):
            features = self.pool(self.backbone(images))
            return self.projector(features.flatten(2).transpose(1, 2))

    class VQAGenModel(nn.Module):
        def __init__(self):
            super().__init__()
            # Construct architecture only; do not download/load base model weights.
            self.seq2seq = AutoModelForSeq2SeqLM.from_config(seq2seq_config)
            self.d_model = self.seq2seq.config.d_model
            self.image_encoder = ImageEncoder(self.d_model, num_visual_tokens)

        def _combine_encoder_inputs(self, images, input_ids, attention_mask):
            visual = self.image_encoder(images)
            text = self.seq2seq.get_input_embeddings()(input_ids)
            visual_mask = torch.ones(
                images.size(0), visual.size(1), dtype=attention_mask.dtype,
                device=attention_mask.device,
            )
            return torch.cat([visual, text], dim=1), torch.cat([visual_mask, attention_mask], dim=1)

        def generate(self, images, input_ids, attention_mask, **kwargs):
            embeds, mask = self._combine_encoder_inputs(images, input_ids, attention_mask)
            outputs = self.seq2seq.get_encoder()(inputs_embeds=embeds, attention_mask=mask)
            return self.seq2seq.generate(encoder_outputs=outputs, attention_mask=mask, **kwargs)

    return VQAGenModel()


class ScratchVIVQAModel(BaseVIVQAModel):
    """Synchronous adapter. No automatic load in predict; lifecycle belongs to manager.

    error_factory(status_code, code, message) can bridge the team's AppError API.
    Default expects AppError(status_code=..., code=..., message=...).
    """
    model_id = "scratch"

    def __init__(self, model_path: str | Path | None = None, device: str | None = None,
                 *, error_factory: Callable[[int, str, str], Exception] | None = None):
        settings = get_settings()
        path = Path(model_path) if model_path is not None else settings.resolved_scratch_model_path
        self.model_path = path if path.is_absolute() else _BACKEND_ROOT / path
        self.device = device if device is not None else settings.AI_DEVICE
        self.device_name = self.device
        self._error_factory = error_factory or _app_error
        self._model = self._tokenizer = self._transform = self._device = None
        self._settings = None
        self._torch = None

    @property
    def _is_loaded(self) -> bool:
        """Compatibility with the scaffold; state is derived from the model reference."""
        return self.loaded

    @property
    def loaded(self) -> bool:
        return self._model is not None

    def artifacts_present(self) -> bool:
        """Lightweight manager preflight; does not assert that load will succeed."""
        try:
            read_manifest(self.model_path)
            return True
        except (OSError, ValueError, TypeError, AttributeError):
            return False

    def _error(self, status: int, code: str, message: str) -> Exception:
        return self._error_factory(status, code, message)

    def load(self) -> None:
        if self.loaded:
            return
        model = tokenizer = transform = checkpoint = None
        failure = False
        try:
            manifest = read_manifest(self.model_path)
            for name, expected in manifest["sha256"].items():
                if _sha256(_local_file(self.model_path, name)) != expected:
                    raise ValueError(f"Checksum mismatch: {name}")
            import torch
            from torchvision import transforms as T
            from transformers import AutoConfig, AutoTokenizer, GenerationConfig
            self._torch = torch
            device = torch.device(self.device_name)
            self._device = device  # cleanup on partial load failure
            if device.type == "cpu":
                if device.index is not None:
                    raise ValueError("Use AI_DEVICE=cpu without an index")
            elif device.type == "cuda":
                if not torch.cuda.is_available():
                    raise ValueError("CUDA is unavailable")
                if device.index is not None and device.index >= torch.cuda.device_count():
                    raise ValueError("CUDA index is unavailable")
            else:
                raise ValueError("Supported devices: cpu, cuda, cuda:N")

            checkpoint = torch.load(self.model_path / "best_vqa_model.pt",
                                    map_location="cpu", weights_only=True)
            settings = _read_settings(checkpoint)
            minimum = manifest["min_new_tokens"]
            if minimum >= settings["GEN_MAX_LENGTH"] - 1:
                raise ValueError("min_new_tokens leaves no space within max_length")
            assets = str(self.model_path / "vit5")
            config = AutoConfig.from_pretrained(assets, local_files_only=True, trust_remote_code=False)
            if config.model_type != "t5":
                raise ValueError("Expected a T5 architecture")
            tokenizer = AutoTokenizer.from_pretrained(
                assets, use_fast=False, local_files_only=True, trust_remote_code=False,
            )
            if tokenizer.padding_side != "right" or tokenizer.truncation_side != "right":
                raise ValueError("Tokenizer must use the notebook's right padding/truncation")
            if (tokenizer.pad_token_id != config.pad_token_id
                    or tokenizer.eos_token_id != config.eos_token_id
                    or len(tokenizer) > config.vocab_size):
                raise ValueError("Tokenizer and T5 config mismatch")
            model = _build_model(config, checkpoint["num_visual_tokens"])
            model.load_state_dict(checkpoint["model_state_dict"], strict=True)
            model.seq2seq.generation_config = GenerationConfig.from_pretrained(
                assets, local_files_only=True,
            )
            checkpoint = None  # drop CPU checkpoint before transfer to GPU
            model.to(device=device, dtype=torch.float32)
            model.eval()
            transform = T.Compose([
                T.Resize((settings["IMG_SIZE"], settings["IMG_SIZE"]),
                         interpolation=T.InterpolationMode.BILINEAR, antialias=True),
                T.ToTensor(), T.Normalize(MEAN, STD),
            ])
            if settings["USE_KB_CONTEXT"]:
                _LOG.warning("Scratch trained with KB context; this adapter uses question-only "
                             "input as in notebook cell 48. Re-evaluate demo quality without KB.")
            settings["min_new_tokens"] = minimum
            self._model, self._tokenizer, self._transform = model, tokenizer, transform
            self._settings = settings
        except Exception:
            # Detailed diagnostics stay in backend logs, not the public message.
            _LOG.exception("Cannot load scratch model")
            failure = True
        if failure:
            # Outside except: traceback no longer retains partially loaded tensors.
            model = tokenizer = transform = checkpoint = None
            self.unload()
            raise self._error(503, "MODEL_UNAVAILABLE", "Model tự xây chưa sẵn sàng.") from None

    def predict(self, image: Image.Image, question: str) -> str:
        """Use loaded model; caller supplies validated NFC/trimmed question and RGB image.

        Does not mutate/close image, lowercase text, inject prompt, or remember history.
        """
        if not self.loaded:
            raise self._error(503, "MODEL_UNAVAILABLE", "Model tự xây chưa được nạp.")
        try:
            from PIL import Image
            if not isinstance(image, Image.Image) or image.mode != "RGB":
                raise ValueError("Adapter expects a loaded RGB PIL image")
            if not isinstance(question, str) or not question.strip():
                raise ValueError("Adapter expects a validated nonempty question")
            config = self._settings
            with self._torch.inference_mode():
                image_t = self._transform(image).unsqueeze(0).to(self._device)
                enc = self._tokenizer(question, padding="max_length", truncation=True,
                                      max_length=config["MAX_QUESTION_LEN"], return_tensors="pt")
                ids = self._model.generate(
                    image_t, enc["input_ids"].to(self._device), enc["attention_mask"].to(self._device),
                    max_length=config["GEN_MAX_LENGTH"], num_beams=config["GEN_NUM_BEAMS"],
                    min_new_tokens=config["min_new_tokens"], do_sample=False,
                    early_stopping=config["GEN_NUM_BEAMS"] > 1,
                )
                text = self._tokenizer.decode(ids[0], skip_special_tokens=True)
                return extract_answer(text, config["ANSWER_MARKER"])
        except Exception:
            _LOG.exception("Scratch inference failed")
        raise self._error(500, "INFERENCE_FAILED", "Không thể sinh câu trả lời từ model tự xây.") from None

    def unload(self) -> None:
        """Idempotent. Call only after actual worker completion, never on HTTP timeout."""
        torch, device = self._torch, self._device
        self._model = self._tokenizer = self._transform = self._device = self._settings = None
        self._torch = None
        gc.collect()
        if torch is not None and device is not None and device.type == "cuda":
            try:
                with torch.cuda.device(device):
                    torch.cuda.empty_cache()
            except Exception:
                _LOG.exception("CUDA cache cleanup failed after releasing scratch references")


# Compatibility for the independent handoff tools; manager uses ScratchVIVQAModel.
ScratchModel = ScratchVIVQAModel
