"""Standalone smoke test: no FastAPI, no manager, no fake answer."""
from __future__ import annotations
import argparse
import importlib.metadata
import json
import logging
from pathlib import Path
import platform
import sys
import threading
import time
import unicodedata

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from app.ai.scratch_model import ScratchModel


class StandaloneError(RuntimeError):
    def __init__(self, status_code, code, message):
        self.status_code, self.code = status_code, code
        super().__init__(message)


class MemorySampler:
    """Sample process RSS, not Python allocations only. Peak is sampled, not exact."""
    def __init__(self):
        import psutil
        self.method = "psutil RSS sampled at 20ms"
        try:
            process = psutil.Process()
            process.memory_info()
            self._read = lambda: process.memory_info().rss
        except psutil.Error:
            # Some containers virtualize PIDs differently from /proc.
            self.method = "/proc/self/status VmRSS sampled at 20ms"
            def read_proc():
                for line in Path("/proc/self/status").read_text().splitlines():
                    if line.startswith("VmRSS:"):
                        return int(line.split()[1]) * 1024
                raise OSError("VmRSS is unavailable")
            self._read = read_proc
        try:
            self.peak = self._read()
        except OSError:
            self.peak = None
            self.method = "unavailable; inference still runs"
        self.stop = threading.Event()
        self.thread = threading.Thread(target=self._sample, daemon=True)

    def _record(self):
        if self.peak is not None:
            try:
                self.peak = max(self.peak, self._read())
            except OSError:
                self.method += "; sampling stopped early"
                self.stop.set()

    def _sample(self):
        while not self.stop.wait(0.02):
            self._record()

    def __enter__(self):
        self.thread.start()
        return self

    def __exit__(self, *args):
        self._record()
        self.stop.set()
        self.thread.join()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model-path", default=None)
    parser.add_argument("--device", default=None, help="cpu | cuda | cuda:N; default AI_DEVICE or cpu")
    parser.add_argument("--image", type=Path, required=True)
    parser.add_argument("--question", required=True)
    parser.add_argument("--reference-answer", help="Answer obtained from AI reference inference on SAME input")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    question = unicodedata.normalize("NFC", args.question).strip()
    if not 1 <= len(question) <= 2000:
        parser.error("Question must have 1..2000 characters after NFC/strip")
    adapter = ScratchModel(args.model_path, args.device, error_factory=StandaloneError)
    if not adapter.artifacts_present():
        print(json.dumps({"status": "BLOCKED", "reason": "Missing/invalid model artifact bundle"}))
        return 2
    image = None
    report = {"status": "FAILED", "python": platform.python_version(), "platform": platform.platform(),
              "device": adapter.device_name, "question": question}
    for package in ("torch", "torchvision", "transformers", "tokenizers", "sentencepiece", "Pillow"):
        try:
            report[package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            report[package] = "missing"
    try:
        from PIL import Image, ImageOps
        import torch
        with Image.open(args.image) as source:
            if source.format not in {"JPEG", "PNG", "WEBP"} or getattr(source, "n_frames", 1) != 1:
                raise ValueError("Expected a static JPEG/PNG/WEBP")
            with ImageOps.exif_transpose(source) as upright:
                if "A" in upright.getbands() or "transparency" in upright.info:
                    with upright.convert("RGBA") as rgba:
                        with Image.new("RGBA", rgba.size, "white") as background:
                            with Image.alpha_composite(background, rgba) as composite:
                                image = composite.convert("RGB")
                else:
                    image = upright.convert("RGB")
        # Only the standalone script handles file I/O; adapter owns no image file.
        cuda = torch.device(adapter.device_name)
        if cuda.type == "cuda" and torch.cuda.is_available():
            torch.cuda.reset_peak_memory_stats(cuda)
        with MemorySampler() as memory:
            start = time.perf_counter()
            adapter.load()
            if cuda.type == "cuda":
                torch.cuda.synchronize(cuda)
            report["load_seconds"] = time.perf_counter() - start
            start = time.perf_counter()
            answer = adapter.predict(image, question)
            if cuda.type == "cuda":
                torch.cuda.synchronize(cuda)
            report["inference_seconds"] = time.perf_counter() - start
            report["answer"] = answer
            report["status"] = "OK"
            if args.reference_answer is not None:
                report["reference_answer_match"] = answer == args.reference_answer
                if not report["reference_answer_match"]:
                    report["status"] = "REFERENCE_MISMATCH"
            if cuda.type == "cuda":
                report["cuda_peak_allocated_mib"] = torch.cuda.max_memory_allocated(cuda) / 2**20
                report["cuda_peak_reserved_mib"] = torch.cuda.max_memory_reserved(cuda) / 2**20
        report["process_peak_rss_sampled_mib"] = memory.peak / 2**20 if memory.peak is not None else None
        report["memory_measurement"] = memory.method
    except Exception as exc:
        logging.exception("Standalone test failed")
        report["error_code"] = getattr(exc, "code", "STANDALONE_FAILED")
    finally:
        adapter.unload()
        adapter.unload()
        report["unloaded"] = not adapter.loaded
        if image is not None:
            image.close()
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["status"] == "OK" else 1


if __name__ == "__main__":
    raise SystemExit(main())
