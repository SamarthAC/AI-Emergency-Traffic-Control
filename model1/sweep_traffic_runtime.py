"""
sweep_traffic_runtime.py

Runtime threshold sweep for normal traffic classes 0-13.

Keeps ambulance handling separate:
    ambulance threshold = 0.70
    ambulance NMS = 0.20
    ambulance containment = 0.80

For each traffic threshold, this script:
- runs V4 once
- reuses the same raw detections
- applies class-aware NMS
- saves an annotated image
- prints vehicle counts and per-class counts

Usage:
    python sweep_traffic_runtime.py auto_test.jpg
"""

from pathlib import Path
from collections import Counter
import argparse

import torch
from PIL import Image, ImageDraw

BASE_DIR = Path(__file__).resolve().parent

from inference_v4 import (
    TrafficInferenceV4,
    letterbox_image,
    decode_head,
    class_aware_nms,
    ambulance_postprocess,
    normalized_to_original_pixels,
    CLASS_NAMES,
)

TRAFFIC_THRESHOLDS = [
    0.55,
    0.60,
    0.65,
    0.70,
    0.75,
    0.80,
]

TRAFFIC_NMS_IOU = 0.40
AMBULANCE_CLASS_ID = 14

# Decode low enough for the full sweep.
RAW_DECODE_THRESHOLD = min(TRAFFIC_THRESHOLDS)


def draw_detections(image, detections, meta, output_path):
    canvas = image.copy()
    draw = ImageDraw.Draw(canvas)

    for detection in detections:
        class_id = detection["class_id"]
        class_name = CLASS_NAMES[class_id]
        confidence = detection["confidence"]

        x1, y1, x2, y2 = normalized_to_original_pixels(
            detection["box"],
            meta,
        )

        draw.rectangle(
            [x1, y1, x2, y2],
            width=3,
        )

        draw.text(
            (x1 + 3, y1 + 3),
            f"{class_name} {confidence:.2f}",
        )

    canvas.save(output_path)


@torch.inference_mode()
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "image",
        type=str,
        help="Traffic image to sweep",
    )
    args = parser.parse_args()

    image_path = Path(args.image)

    if not image_path.exists():
        raise FileNotFoundError(image_path)

    detector = TrafficInferenceV4()

    image = Image.open(image_path).convert("RGB")
    tensor, meta = letterbox_image(image)

    batch = tensor.unsqueeze(0).to(detector.device)

    if detector.device.type == "cuda":
        with torch.amp.autocast(device_type="cuda"):
            outputs = detector.model(batch)
    else:
        outputs = detector.model(batch)

    raw_detections = []

    for head_name in ("small", "large"):
        prediction = (
            outputs[head_name][0]
            .detach()
            .float()
            .cpu()
        )

        raw_detections.extend(
            decode_head(
                prediction,
                RAW_DECODE_THRESHOLD,
            )
        )

    ambulance = ambulance_postprocess(
        raw_detections
    )

    print("=" * 100)
    print("V4 NORMAL-TRAFFIC RUNTIME THRESHOLD SWEEP")
    print("=" * 100)
    print("Image:", image_path.name)
    print("Device:", detector.device)
    print("Traffic NMS IoU:", TRAFFIC_NMS_IOU)
    print("Ambulance detections kept separately:", len(ambulance))
    print()

    for threshold in TRAFFIC_THRESHOLDS:
        traffic = [
            detection
            for detection in raw_detections
            if (
                detection["class_id"] != AMBULANCE_CLASS_ID
                and detection["confidence"] >= threshold
            )
        ]

        traffic = class_aware_nms(
            traffic,
            TRAFFIC_NMS_IOU,
        )

        combined = traffic + ambulance
        combined.sort(
            key=lambda detection: detection["confidence"],
            reverse=True,
        )

        counts = Counter(
            CLASS_NAMES[detection["class_id"]]
            for detection in traffic
        )

        output_dir = BASE_DIR / "traffic_sweep_results"
        output_dir.mkdir(parents=True, exist_ok=True)

        output_path = (
            output_dir
            / f"{image_path.stem}_traffic_t{int(threshold * 100):02d}.jpg"
        )

        draw_detections(
            image,
            combined,
            meta,
            output_path,
        )

        print(
            f"Threshold {threshold:.2f} | "
            f"normal traffic={len(traffic):>3} | "
            f"ambulance={len(ambulance):>2} | "
            f"total={len(combined):>3}"
        )

        if counts:
            print(
                "  "
                + ", ".join(
                    f"{name}={count}"
                    for name, count in sorted(counts.items())
                )
            )
        else:
            print("  no normal traffic detections")

        print("  saved:", output_path.name)

    print()
    print("=" * 100)
    print("Compare the six output images visually.")
    print("Choose the lowest threshold that improves recall")
    print("without creating obvious duplicate/false boxes.")
    print("=" * 100)


if __name__ == "__main__":
    main()
