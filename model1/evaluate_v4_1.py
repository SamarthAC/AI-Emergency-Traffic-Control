"""
V4.1 evaluation launcher.

This intentionally reuses the already-validated evaluate_v4.py evaluator and
changes ONLY the model checkpoint to traffic_detector_v4_1_best.pth.

Why:
- keeps V4 evaluation rules identical
- avoids duplicating decoder / NMS / IoU / matching logic
- leaves evaluate_v4.py untouched
"""

from pathlib import Path
import evaluate_v4 as ev


MODEL_DIR = Path(__file__).resolve().parent
V4_1_MODEL = MODEL_DIR / "traffic_detector_v4_1_best.pth"


def main():
    if not V4_1_MODEL.exists():
        raise FileNotFoundError(
            "V4.1 best model not found:\n"
            f"{V4_1_MODEL}"
        )

    # Override only the checkpoint path.
    ev.MODEL_PATH = V4_1_MODEL

    print("=" * 100)
    print("V4.1 EVALUATION")
    print("=" * 100)
    print("Model:", ev.MODEL_PATH)
    print("Using the same evaluator / decoder / matching rules as V4.")
    print("=" * 100)

    # evaluate_v4.py already owns the tested evaluation pipeline.
    # Its main() loads MODEL_PATH at runtime, so the override above
    # makes it evaluate V4.1 without modifying the original file.
    ev.main()


if __name__ == "__main__":
    main()
