"""
calibrate_ambulance_runtime.py

Batch-calibrate the runtime ambulance threshold using unseen images.

Expected folder structure (relative to this script):
    runtime_test/
        ambulance/
            amb1.jpg
            ...
        normal/
            normal1.jpg
            ...

The script:
1. Runs the final V4 model on every image.
2. Computes the strongest ambulance-specific score anywhere in either head:
       objectness * P(ambulance)
3. Evaluates candidate thresholds.
4. Reports TP / FP / TN / FN, precision, recall, F1, accuracy.
5. Recommends:
   - Best-F1 threshold
   - Highest-recall threshold with zero false positives, if one exists
6. Saves a CSV for inspection.

IMPORTANT:
This is runtime calibration only. It does NOT change the official validation metrics.
"""

from pathlib import Path
import csv
import math

import torch
from PIL import Image

from inference_v4 import (
    TrafficInferenceV4,
    letterbox_image,
    CLASS_NAMES,
)


BASE_DIR = Path(__file__).resolve().parent
AMBULANCE_DIR = BASE_DIR / "runtime_test" / "ambulance"
NORMAL_DIR = BASE_DIR / "runtime_test" / "normal"

AMBULANCE_CLASS_ID = 14

SUPPORTED_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".bmp",
    ".webp",
}

# Broad sweep so we do not guess.
THRESHOLDS = [
    round(x / 100.0, 2)
    for x in range(30, 100)
]


def list_images(folder):
    if not folder.exists():
        raise FileNotFoundError(
            f"Folder not found:\n{folder}"
        )

    return sorted([
        path
        for path in folder.iterdir()
        if (
            path.is_file()
            and path.suffix.lower()
            in SUPPORTED_EXTENSIONS
        )
    ])


def safe_divide(numerator, denominator):
    if denominator == 0:
        return 0.0

    return numerator / denominator


def calculate_metrics(
    records,
    threshold,
):
    tp = 0
    fp = 0
    tn = 0
    fn = 0

    for record in records:
        predicted_positive = (
            record["best_ambulance_score"]
            >= threshold
        )

        actual_positive = (
            record["label"]
            == 1
        )

        if (
            predicted_positive
            and actual_positive
        ):
            tp += 1

        elif (
            predicted_positive
            and not actual_positive
        ):
            fp += 1

        elif (
            not predicted_positive
            and actual_positive
        ):
            fn += 1

        else:
            tn += 1

    precision = safe_divide(
        tp,
        tp + fp,
    )

    recall = safe_divide(
        tp,
        tp + fn,
    )

    f1 = safe_divide(
        2.0
        * precision
        * recall,
        precision + recall,
    )

    accuracy = safe_divide(
        tp + tn,
        tp + fp + tn + fn,
    )

    specificity = safe_divide(
        tn,
        tn + fp,
    )

    return {
        "threshold": threshold,
        "tp": tp,
        "fp": fp,
        "tn": tn,
        "fn": fn,
        "precision": precision,
        "recall": recall,
        "specificity": specificity,
        "f1": f1,
        "accuracy": accuracy,
    }


@torch.inference_mode()
def get_best_ambulance_score(
    detector,
    image_path,
):
    image = Image.open(
        image_path
    ).convert("RGB")

    tensor, _ = letterbox_image(
        image
    )

    batch = (
        tensor
        .unsqueeze(0)
        .to(
            detector.device
        )
    )

    if detector.device.type == "cuda":
        with torch.amp.autocast(
            device_type="cuda"
        ):
            outputs = detector.model(
                batch
            )
    else:
        outputs = detector.model(
            batch
        )

    best_score = -1.0
    best_objectness = 0.0
    best_ambulance_probability = 0.0
    winning_class_id_at_best = -1
    winning_class_probability_at_best = 0.0
    best_head = None
    best_row = -1
    best_col = -1

    for head_name in (
        "small",
        "large",
    ):
        prediction = (
            outputs[
                head_name
            ][0]
            .detach()
            .float()
            .cpu()
        )

        objectness = torch.sigmoid(
            prediction[0]
        )

        class_probabilities = torch.softmax(
            prediction[5:],
            dim=0,
        )

        ambulance_probability = (
            class_probabilities[
                AMBULANCE_CLASS_ID
            ]
        )

        ambulance_score = (
            objectness
            * ambulance_probability
        )

        flat_index = int(
            torch.argmax(
                ambulance_score
            ).item()
        )

        grid_height, grid_width = (
            ambulance_score.shape
        )

        row = (
            flat_index
            // grid_width
        )

        col = (
            flat_index
            % grid_width
        )

        score = float(
            ambulance_score[
                row,
                col
            ].item()
        )

        if score > best_score:
            best_score = score

            best_objectness = float(
                objectness[
                    row,
                    col
                ].item()
            )

            best_ambulance_probability = float(
                ambulance_probability[
                    row,
                    col
                ].item()
            )

            (
                winning_class_probability,
                winning_class_id,
            ) = torch.max(
                class_probabilities[
                    :,
                    row,
                    col
                ],
                dim=0,
            )

            winning_class_id_at_best = int(
                winning_class_id.item()
            )

            winning_class_probability_at_best = float(
                winning_class_probability.item()
            )

            best_head = head_name
            best_row = row
            best_col = col

    return {
        "best_ambulance_score":
            best_score,
        "objectness":
            best_objectness,
        "ambulance_probability":
            best_ambulance_probability,
        "winning_class_id":
            winning_class_id_at_best,
        "winning_class_name":
            (
                CLASS_NAMES[
                    winning_class_id_at_best
                ]
                if (
                    0
                    <= winning_class_id_at_best
                    < len(CLASS_NAMES)
                )
                else "Unknown"
            ),
        "winning_class_probability":
            winning_class_probability_at_best,
        "head":
            best_head,
        "row":
            best_row,
        "col":
            best_col,
    }


def choose_best_f1(
    results
):
    return max(
        results,
        key=lambda result: (
            result["f1"],
            result["recall"],
            result["precision"],
            result["threshold"],
        )
    )


def choose_zero_fp(
    results
):
    candidates = [
        result
        for result in results
        if result["fp"] == 0
    ]

    if not candidates:
        return None

    return max(
        candidates,
        key=lambda result: (
            result["recall"],
            result["f1"],
            -result["threshold"],
        )
    )


def print_metric_row(result):
    print(
        f"{result['threshold']:<10.2f}"
        f"{result['tp']:<6}"
        f"{result['fp']:<6}"
        f"{result['tn']:<6}"
        f"{result['fn']:<6}"
        f"{result['precision']:<11.4f}"
        f"{result['recall']:<11.4f}"
        f"{result['f1']:<11.4f}"
        f"{result['accuracy']:<11.4f}"
    )


def main():
    ambulance_images = list_images(
        AMBULANCE_DIR
    )

    normal_images = list_images(
        NORMAL_DIR
    )

    if len(ambulance_images) == 0:
        raise RuntimeError(
            "No ambulance images found in:\n"
            f"{AMBULANCE_DIR}"
        )

    if len(normal_images) == 0:
        raise RuntimeError(
            "No normal images found in:\n"
            f"{NORMAL_DIR}"
        )

    detector = TrafficInferenceV4()

    print(
        "=" * 110
    )
    print(
        "V4 RUNTIME AMBULANCE CALIBRATION"
    )
    print(
        "=" * 110
    )
    print(
        "Device:",
        detector.device
    )
    print(
        "Ambulance images:",
        len(ambulance_images)
    )
    print(
        "Normal images   :",
        len(normal_images)
    )
    print()

    records = []

    all_images = (
        [
            (
                path,
                1,
                "ambulance",
            )
            for path
            in ambulance_images
        ]
        +
        [
            (
                path,
                0,
                "normal",
            )
            for path
            in normal_images
        ]
    )

    total = len(
        all_images
    )

    for index, (
        image_path,
        label,
        label_name,
    ) in enumerate(
        all_images,
        start=1,
    ):
        diagnostic = (
            get_best_ambulance_score(
                detector,
                image_path,
            )
        )

        record = {
            "filename":
                image_path.name,
            "label":
                label,
            "label_name":
                label_name,
            **diagnostic,
        }

        records.append(
            record
        )

        print(
            f"[{index:>2}/{total}] "
            f"{label_name:<10} "
            f"{image_path.name:<30} "
            f"score="
            f"{record['best_ambulance_score']:.4f} "
            f"obj="
            f"{record['objectness']:.4f} "
            f"ambProb="
            f"{record['ambulance_probability']:.4f} "
            f"winner="
            f"{record['winning_class_name']}"
        )

    print(
        "\n"
        + "=" * 110
    )
    print(
        "IMAGE-LEVEL SCORES"
    )
    print(
        "=" * 110
    )

    sorted_records = sorted(
        records,
        key=lambda record: (
            -record["label"],
            -record[
                "best_ambulance_score"
            ],
        )
    )

    print(
        f"{'Label':<12}"
        f"{'Image':<32}"
        f"{'AmbScore':<12}"
        f"{'Objectness':<12}"
        f"{'AmbProb':<12}"
        f"{'Winner':<20}"
    )

    print(
        "-" * 100
    )

    for record in sorted_records:
        print(
            f"{record['label_name']:<12}"
            f"{record['filename']:<32}"
            f"{record['best_ambulance_score']:<12.4f}"
            f"{record['objectness']:<12.4f}"
            f"{record['ambulance_probability']:<12.4f}"
            f"{record['winning_class_name']:<20}"
        )

    results = [
        calculate_metrics(
            records,
            threshold,
        )
        for threshold
        in THRESHOLDS
    ]

    best_f1 = choose_best_f1(
        results
    )

    zero_fp = choose_zero_fp(
        results
    )

    positive_scores = [
        record[
            "best_ambulance_score"
        ]
        for record
        in records
        if record["label"] == 1
    ]

    negative_scores = [
        record[
            "best_ambulance_score"
        ]
        for record
        in records
        if record["label"] == 0
    ]

    min_positive = min(
        positive_scores
    )

    max_negative = max(
        negative_scores
    )

    print(
        "\n"
        + "=" * 110
    )
    print(
        "SEPARATION SUMMARY"
    )
    print(
        "=" * 110
    )

    print(
        "Lowest ambulance-image score :",
        f"{min_positive:.4f}"
    )

    print(
        "Highest normal-image score    :",
        f"{max_negative:.4f}"
    )

    if min_positive > max_negative:
        midpoint = (
            min_positive
            + max_negative
        ) / 2.0

        print(
            "Clean separation             : YES"
        )

        print(
            "Midpoint between classes     :",
            f"{midpoint:.4f}"
        )

    else:
        print(
            "Clean separation             : NO"
        )

        print(
            "Score overlap                :",
            f"{max_negative - min_positive:.4f}"
        )

    print(
        "\n"
        + "=" * 110
    )
    print(
        "MOST RELEVANT THRESHOLDS"
    )
    print(
        "=" * 110
    )

    print(
        f"{'Threshold':<10}"
        f"{'TP':<6}"
        f"{'FP':<6}"
        f"{'TN':<6}"
        f"{'FN':<6}"
        f"{'Precision':<11}"
        f"{'Recall':<11}"
        f"{'F1':<11}"
        f"{'Accuracy':<11}"
    )

    print(
        "-" * 90
    )

    interesting_thresholds = {
        0.60,
        0.65,
        0.70,
        0.75,
        0.80,
        0.85,
        0.90,
        round(
            best_f1[
                "threshold"
            ],
            2,
        ),
    }

    if zero_fp is not None:
        interesting_thresholds.add(
            round(
                zero_fp[
                    "threshold"
                ],
                2,
            )
        )

    for result in results:
        if (
            round(
                result["threshold"],
                2,
            )
            in interesting_thresholds
        ):
            print_metric_row(
                result
            )

    print(
        "\n"
        + "=" * 110
    )
    print(
        "RECOMMENDATIONS"
    )
    print(
        "=" * 110
    )

    print(
        "\nBest F1 threshold:"
    )
    print_metric_row(
        best_f1
    )

    if zero_fp is not None:
        print(
            "\nBest threshold with ZERO false "
            "positives on this calibration set:"
        )
        print_metric_row(
            zero_fp
        )
    else:
        print(
            "\nNo threshold in the sweep achieved "
            "zero false positives while detecting "
            "at least one ambulance."
        )

    output_csv = (
        BASE_DIR
        / "runtime_ambulance_calibration.csv"
    )

    with open(
        output_csv,
        "w",
        newline="",
        encoding="utf-8",
    ) as file:
        fieldnames = [
            "filename",
            "label_name",
            "best_ambulance_score",
            "objectness",
            "ambulance_probability",
            "winning_class_name",
            "winning_class_probability",
            "head",
            "row",
            "col",
        ]

        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames,
        )

        writer.writeheader()

        for record in records:
            writer.writerow({
                field:
                    record[field]
                for field
                in fieldnames
            })

    print(
        "\nCSV saved:",
        output_csv
    )

    print(
        "\nNOTE:"
    )
    print(
        "Do NOT overwrite official validation metrics "
        "with these runtime-calibration results."
    )
    print(
        "Use this only to choose the live-system threshold."
    )

    print(
        "=" * 110
    )


if __name__ == "__main__":
    main()
