
from pathlib import Path
import argparse
import torch
from PIL import Image

from inference_v4 import (
    TrafficInferenceV4,
    letterbox_image,
    decode_head,
    CLASS_NAMES,
)

DIAGNOSTIC_DECODE_THRESHOLD = 0.05
AMBULANCE_CLASS_ID = 14
TOP_K_AMBULANCE_CELLS = 10
TOP_K_RAW_DETECTIONS = 25


def analyze_head(prediction, head_name):
    objectness = torch.sigmoid(prediction[0])
    class_probs = torch.softmax(prediction[5:], dim=0)

    ambulance_prob = class_probs[AMBULANCE_CLASS_ID]
    ambulance_score = objectness * ambulance_prob

    best_class_prob, best_class_id = torch.max(class_probs, dim=0)
    best_score = objectness * best_class_prob

    flat_scores = ambulance_score.flatten()
    k = min(TOP_K_AMBULANCE_CELLS, flat_scores.numel())
    top_values, top_indices = torch.topk(flat_scores, k=k)

    _, grid_w = ambulance_score.shape
    ambulance_rows = []

    for score, flat_index in zip(top_values.tolist(), top_indices.tolist()):
        row = flat_index // grid_w
        col = flat_index % grid_w
        winning_class = int(best_class_id[row, col].item())

        ambulance_rows.append({
            "head": head_name,
            "row": row,
            "col": col,
            "ambulance_score": float(score),
            "objectness": float(objectness[row, col].item()),
            "ambulance_probability": float(ambulance_prob[row, col].item()),
            "winning_class_id": winning_class,
            "winning_class_name": CLASS_NAMES[winning_class],
            "winning_class_probability": float(best_class_prob[row, col].item()),
            "winning_confidence": float(best_score[row, col].item()),
        })

    raw = decode_head(prediction, DIAGNOSTIC_DECODE_THRESHOLD)
    return ambulance_rows, raw


@torch.inference_mode()
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("image", type=str)
    args = parser.parse_args()

    image_path = Path(args.image)
    if not image_path.exists():
        raise FileNotFoundError(image_path)

    detector = TrafficInferenceV4()

    image = Image.open(image_path).convert("RGB")
    tensor, _ = letterbox_image(image)

    debug_input_path = image_path.parent / f"{image_path.stem}_letterboxed_448.jpg"

    arr = (
        tensor.permute(1, 2, 0)
        .mul(255.0)
        .clamp(0, 255)
        .byte()
        .cpu()
        .numpy()
    )
    Image.fromarray(arr).save(debug_input_path)

    batch = tensor.unsqueeze(0).to(detector.device)

    if detector.device.type == "cuda":
        with torch.amp.autocast(device_type="cuda"):
            outputs = detector.model(batch)
    else:
        outputs = detector.model(batch)

    all_ambulance_rows = []
    all_raw = []

    for head_name in ("small", "large"):
        prediction = outputs[head_name][0].detach().float().cpu()

        ambulance_rows, raw = analyze_head(prediction, head_name)
        all_ambulance_rows.extend(ambulance_rows)

        for detection in raw:
            d = dict(detection)
            d["head"] = head_name
            all_raw.append(d)

    all_ambulance_rows.sort(
        key=lambda row: row["ambulance_score"],
        reverse=True,
    )
    all_raw.sort(
        key=lambda d: d["confidence"],
        reverse=True,
    )

    print("=" * 100)
    print("V4 SINGLE-IMAGE DIAGNOSTIC")
    print("=" * 100)
    print("Image:", image_path)
    print("Device:", detector.device)
    print("CNN input saved:", debug_input_path)

    print("\nTOP AMBULANCE-SPECIFIC CELLS")
    print("-" * 100)

    for index, row in enumerate(all_ambulance_rows[:TOP_K_AMBULANCE_CELLS], start=1):
        print(
            f"{index:02d}. {row['head']:<5} "
            f"cell=({row['row']},{row['col']}) | "
            f"AMB_SCORE={row['ambulance_score']:.4f} "
            f"obj={row['objectness']:.4f} "
            f"ambProb={row['ambulance_probability']:.4f} | "
            f"winner={row['winning_class_name']} "
            f"winnerProb={row['winning_class_probability']:.4f} "
            f"winnerConf={row['winning_confidence']:.4f}"
        )

    best_ambulance = all_ambulance_rows[0]

    print(
        "\nBEST AMBULANCE-SPECIFIC SCORE:",
        f"{best_ambulance['ambulance_score']:.4f}"
    )
    print(
        "Winning class at that cell:",
        best_ambulance["winning_class_name"]
    )

    if (
        best_ambulance["ambulance_score"] >= 0.96
        and best_ambulance["winning_class_id"] == AMBULANCE_CLASS_ID
    ):
        print(
            "Diagnosis: model strongly recognizes an ambulance "
            "at the current deployment threshold."
        )
    elif best_ambulance["winning_class_id"] == AMBULANCE_CLASS_ID:
        print(
            "Diagnosis: Ambulance IS the winning class, "
            "but confidence is below 0.96."
        )
    else:
        print(
            "Diagnosis: Ambulance is NOT the winning class at the strongest "
            "ambulance-like cell. This is not merely a threshold problem."
        )

    print(
        f"\nTOP RAW BEST-CLASS DETECTIONS "
        f"(diagnostic threshold >= {DIAGNOSTIC_DECODE_THRESHOLD:.2f})"
    )
    print("-" * 100)

    if not all_raw:
        print("No raw detections >= diagnostic threshold.")
    else:
        for index, detection in enumerate(all_raw[:TOP_K_RAW_DETECTIONS], start=1):
            class_id = detection["class_id"]
            print(
                f"{index:02d}. "
                f"{CLASS_NAMES[class_id]:<18} "
                f"conf={detection['confidence']:.4f} "
                f"head={detection['head']:<5} "
                f"box={tuple(round(v, 4) for v in detection['box'])}"
            )

    print("\nCURRENT DEPLOYMENT THRESHOLDS")
    print("Normal traffic : 0.80")
    print("Ambulance      : 0.96")
    print("=" * 100)


if __name__ == "__main__":
    main()
