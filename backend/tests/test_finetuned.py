"""Standalone smoke test for Minh's Vintern-1B-v2 .pt checkpoint.

From backend/: python scripts/test_finetuned.py IMAGE "QUESTION"
Requires base model files via VINTERN_BASE and best_vintern_vqa.pt via FINETUNED_MODEL_PATH.
"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PIL import Image
from app.ai.finetuned_model import FinetunedVIVQAModel
from app.errors import AppError


def main() -> int:
    if len(sys.argv) < 3:
        print(__doc__)
        return 2
    with Image.open(sys.argv[1]) as source:
        image = source.convert("RGB")
    question = sys.argv[2]
    model = FinetunedVIVQAModel()
    print(f"[info] checkpoint={model._checkpoint_file()} base={model.base_model} device={model.device}")
    try:
        start = time.time()
        model.load()
        print(f"[ok] load: {time.time() - start:.1f}s")
        for index in range(2):
            start = time.time()
            answer = model.predict(image, question)
            print(f"[ok] predict #{index + 1}: {time.time() - start:.1f}s -> {answer!r}")
            assert isinstance(answer, str) and answer.strip()
        image.load()
        model.unload()
        model.unload()
        assert not model._is_loaded
        print("[ok] unload x2; input image remains open")
        return 0
    except AppError as exc:
        print(f"[error] {exc.code} ({exc.status_code}): {exc.message}")
        return 1
    finally:
        image.close()
        model.unload()


if __name__ == "__main__":
    raise SystemExit(main())
