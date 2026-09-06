"""
compare_ambulance_postprocess.py

Fair ambulance post-processing comparison:
    V4 vs V4.1

Important:
- Official GT matching remains IoU >= 0.50.
- Same decoder/evaluation functions are reused from evaluate_v4.py.
- Directional containment is used:
      intersection(kept, candidate) / area(candidate)
  This suppresses a lower-confidence candidate only when the candidate itself
  is mostly inside an already-kept detection.
- No model files are modified.
"""

from pathlib import Path
import torch

import evaluate_v4 as ev


# ==========================================================
# CONFIG
# ==========================================================

MODEL_DIR = Path(__file__).resolve().parent

MODELS = {
    "V4": MODEL_DIR / "traffic_detector_v4_best.pth",
    "V4.1": MODEL_DIR / "traffic_detector_v4_1_best.pth",
}

AMBULANCE_CLASS_ID = 14
MATCH_IOU = 0.50

# Include the regions that mattered in the previous sweep.
CONF_THRESHOLDS = [0.94, 0.95, 0.96, 0.97, 0.98]
NMS_THRESHOLDS = [0.40, 0.35, 0.30, 0.25, 0.20]
CONTAINMENT_THRESHOLDS = [None, 0.70, 0.80, 0.90]

# Decode once at a permissive threshold, then filter cached detections.
CACHE_CONFIDENCE = 0.90


# ==========================================================
# BOX HELPERS
# ==========================================================

def box_area(box):
    x1, y1, x2, y2 = box
    return max(0.0, x2 - x1) * max(0.0, y2 - y1)


def intersection_area(a, b):
    x1 = max(a[0], b[0])
    y1 = max(a[1], b[1])
    x2 = min(a[2], b[2])
    y2 = min(a[3], b[3])
    return max(0.0, x2 - x1) * max(0.0, y2 - y1)


def directional_candidate_containment(kept_box, candidate_box):
    """
    Fraction of the LOWER-CONFIDENCE candidate contained inside kept_box.

    This is intentionally NOT:
        intersection / min(area(a), area(b))

    because that symmetric version can suppress a correct larger whole-object
    candidate merely because a small fragment lies inside it.
    """
    candidate_area = box_area(candidate_box)
    if candidate_area <= 0.0:
        return 0.0

    return intersection_area(kept_box, candidate_box) / candidate_area


def iou(a, b):
    inter = intersection_area(a, b)
    union = box_area(a) + box_area(b) - inter
    return inter / union if union > 0.0 else 0.0


# ==========================================================
# NORMALIZATION
# ==========================================================

def normalize_detection(d):
    """
    Supports common detection representations used by our V4 scripts.
    Returns:
        {"box":[x1,y1,x2,y2], "confidence":float, "class_id":int}
    """
    if isinstance(d, dict):
        box = d.get("box", d.get("bbox"))
        conf = d.get("confidence", d.get("score", d.get("conf")))
        cls = d.get("class_id", d.get("class", d.get("category")))

        if box is None or conf is None or cls is None:
            raise ValueError(f"Unsupported detection dictionary: {d}")

        return {
            "box": [float(x) for x in box],
            "confidence": float(conf),
            "class_id": int(cls),
        }

    if isinstance(d, (list, tuple)) and len(d) >= 6:
        return {
            "box": [float(x) for x in d[:4]],
            "confidence": float(d[4]),
            "class_id": int(d[5]),
        }

    raise ValueError(f"Unsupported detection format: {type(d)} -> {d}")


# ==========================================================
# POST-PROCESSING
# ==========================================================

def nms_and_directional_containment(
    detections,
    nms_iou_threshold,
    containment_threshold,
):
    detections = sorted(
        detections,
        key=lambda x: x["confidence"],
        reverse=True,
    )

    kept = []

    while detections:
        best = detections.pop(0)
        kept.append(best)

        survivors = []

        for candidate in detections:
            # Ambulance-only evaluation, but keep this class-safe.
            if candidate["class_id"] != best["class_id"]:
                survivors.append(candidate)
                continue

            if iou(best["box"], candidate["box"]) >= nms_iou_threshold:
                continue

            if containment_threshold is not None:
                contained_fraction = directional_candidate_containment(
                    best["box"],
                    candidate["box"],
                )

                if contained_fraction >= containment_threshold:
                    continue

            survivors.append(candidate)

        detections = survivors

    return kept


# ==========================================================
# OFFICIAL MATCHING
# ==========================================================

def match_image(predictions, ground_truth):
    """
    Greedy one-to-one same-class ambulance matching at official IoU=0.50.
    """
    predictions = sorted(
        predictions,
        key=lambda x: x["confidence"],
        reverse=True,
    )

    matched_gt = set()
    tp = 0
    fp = 0
    matched_iou_sum = 0.0

    for pred in predictions:
        best_gt_index = -1
        best_iou = 0.0

        for gt_index, gt_box in enumerate(ground_truth):
            if gt_index in matched_gt:
                continue

            current_iou = iou(pred["box"], gt_box)

            if current_iou > best_iou:
                best_iou = current_iou
                best_gt_index = gt_index

        if best_gt_index >= 0 and best_iou >= MATCH_IOU:
            matched_gt.add(best_gt_index)
            tp += 1
            matched_iou_sum += best_iou
        else:
            fp += 1

    fn = len(ground_truth) - len(matched_gt)

    return tp, fp, fn, matched_iou_sum


# ==========================================================
# ADAPTERS TO EXISTING EVALUATOR
# ==========================================================

def load_model(model_path, device):
    old_path = ev.MODEL_PATH
    ev.MODEL_PATH = model_path

    try:
        model = ev.load_best_model(device)
    finally:
        ev.MODEL_PATH = old_path

    return model


def ambulance_loader(device):
    # Reuse the validated dataset/loader implementation.
    return ev.make_loader(
        ev.AMBULANCE_IMAGE_DIR,
        ev.AMBULANCE_LABEL_DIR,
        device,
    )


def extract_gt_ambulances(boxes, categories):
    gt = []

    for box, category in zip(boxes, categories):
        if int(category.item()) != AMBULANCE_CLASS_ID:
            continue

        # Dataset boxes are normalized [x, y, w, h].
        x, y, w, h = [float(v) for v in box.tolist()]

        gt.append([
            x,
            y,
            x + w,
            y + h,
        ])

    return gt


def decode_predictions(outputs, confidence_threshold):
    """
    evaluate_v4.py has already been validated in the project, but function
    naming can vary between pasted revisions. Try the expected decoder names
    without changing its implementation.
    """
    candidates = [
        "decode_predictions",
        "decode_multiscale_predictions",
        "decode_model_predictions",
    ]

    decoder = None

    for name in candidates:
        if hasattr(ev, name):
            decoder = getattr(ev, name)
            break

    if decoder is None:
        raise AttributeError(
            "Could not find the prediction decoder in evaluate_v4.py.\n"
            "Expected one of: " + ", ".join(candidates)
        )

    # Try common signatures used by the V4 evaluator.
    attempts = [
        lambda: decoder(outputs, confidence_threshold),
        lambda: decoder(outputs, conf_threshold=confidence_threshold),
        lambda: decoder(outputs, confidence_threshold=confidence_threshold),
        lambda: decoder(outputs, confidence_threshold, 1.0),
    ]

    last_error = None

    for attempt in attempts:
        try:
            return attempt()
        except TypeError as error:
            last_error = error

    raise TypeError(
        "Found the V4 decoder but could not match its call signature.\n"
        f"Last error: {last_error}"
    )


# ==========================================================
# CACHE RAW PREDICTIONS
# ==========================================================

@torch.inference_mode()
def build_cache(model, device):
    dataset, loader = ambulance_loader(device)

    cache = []

    print("Ambulance validation images:", len(dataset))

    processed = 0

    for images, boxes_batch, categories_batch, supervision_batch in loader:
        images = images.to(device, non_blocking=True)
        outputs = model(images)

        decoded_batch = decode_predictions(
            outputs,
            CACHE_CONFIDENCE,
        )

        for detections, boxes, categories in zip(
            decoded_batch,
            boxes_batch,
            categories_batch,
        ):
            normalized = [
                normalize_detection(d)
                for d in detections
                if int(normalize_detection(d)["class_id"]) == AMBULANCE_CLASS_ID
            ]

            gt = extract_gt_ambulances(
                boxes,
                categories,
            )

            cache.append({
                "detections": normalized,
                "gt": gt,
            })

        processed += images.shape[0]

        if processed % 100 < images.shape[0]:
            print(f"Cached {processed}/{len(dataset)}")

    return cache


# ==========================================================
# SWEEP
# ==========================================================

def evaluate_config(cache, conf, nms_iou, containment):
    tp = fp = fn = 0
    matched_iou_sum = 0.0
    total_abs_count_error = 0

    for item in cache:
        detections = [
            d for d in item["detections"]
            if d["confidence"] >= conf
        ]

        detections = nms_and_directional_containment(
            detections,
            nms_iou_threshold=nms_iou,
            containment_threshold=containment,
        )

        image_tp, image_fp, image_fn, image_iou_sum = match_image(
            detections,
            item["gt"],
        )

        tp += image_tp
        fp += image_fp
        fn += image_fn
        matched_iou_sum += image_iou_sum

        total_abs_count_error += abs(
            len(detections) - len(item["gt"])
        )

    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = (
        2.0 * precision * recall / (precision + recall)
        if (precision + recall)
        else 0.0
    )

    count_mae = (
        total_abs_count_error / len(cache)
        if cache
        else 0.0
    )

    mean_tp_iou = (
        matched_iou_sum / tp
        if tp
        else 0.0
    )

    return {
        "conf": conf,
        "nms": nms_iou,
        "containment": containment,
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "count_mae": count_mae,
        "mean_tp_iou": mean_tp_iou,
    }


def sweep_model(name, model_path, device):
    print("\n" + "=" * 110)
    print(f"{name} — CORRECTED AMBULANCE POST-PROCESSING SWEEP")
    print("=" * 110)
    print("Checkpoint:", model_path)

    model = load_model(model_path, device)
    cache = build_cache(model, device)

    results = []

    for conf in CONF_THRESHOLDS:
        for nms in NMS_THRESHOLDS:
            for containment in CONTAINMENT_THRESHOLDS:
                results.append(
                    evaluate_config(
                        cache,
                        conf,
                        nms,
                        containment,
                    )
                )

    results.sort(
        key=lambda r: (
            r["f1"],
            r["recall"],
            r["precision"],
        ),
        reverse=True,
    )

    print("\nTOP 10")
    print("-" * 110)

    for rank, r in enumerate(results[:10], start=1):
        containment_text = (
            "None"
            if r["containment"] is None
            else f"{r['containment']:.2f}"
        )

        print(
            f"{rank:2d}. "
            f"conf={r['conf']:.2f} "
            f"nms={r['nms']:.2f} "
            f"contain={containment_text:>4} | "
            f"TP={r['tp']:3d} FP={r['fp']:3d} FN={r['fn']:3d} | "
            f"P={r['precision']:.4f} "
            f"R={r['recall']:.4f} "
            f"F1={r['f1']:.4f} | "
            f"CountMAE={r['count_mae']:.2f} "
            f"MeanTP-IoU={r['mean_tp_iou']:.4f}"
        )

    best = results[0]

    print("\nBEST", name)
    print("-" * 110)
    print(f"Confidence          : {best['conf']:.2f}")
    print(f"NMS IoU             : {best['nms']:.2f}")
    print(f"Directional contain : {best['containment']}")
    print(f"TP / FP / FN        : {best['tp']} / {best['fp']} / {best['fn']}")
    print(f"Precision           : {best['precision']:.4f}")
    print(f"Recall              : {best['recall']:.4f}")
    print(f"F1                  : {best['f1']:.4f}")
    print(f"Count MAE           : {best['count_mae']:.4f}")
    print(f"Mean TP IoU         : {best['mean_tp_iou']:.4f}")

    del model

    if device.type == "cuda":
        torch.cuda.empty_cache()

    return best


# ==========================================================
# MAIN
# ==========================================================

def main():
    for name, path in MODELS.items():
        if not path.exists():
            raise FileNotFoundError(
                f"{name} checkpoint not found:\n{path}"
            )

    device = torch.device(
        "cuda" if torch.cuda.is_available() else "cpu"
    )

    print("=" * 110)
    print("FINAL FAIR AMBULANCE COMPARISON — V4 vs V4.1")
    print("=" * 110)
    print("Device             :", device)
    print("Official match IoU :", MATCH_IOU)
    print("Containment rule   : intersection / area(lower-confidence candidate)")
    print("Models are NOT modified.")
    print("=" * 110)

    final = {}

    for name, model_path in MODELS.items():
        final[name] = sweep_model(
            name,
            model_path,
            device,
        )

    print("\n" + "=" * 110)
    print("FINAL CORRECTED COMPARISON")
    print("=" * 110)

    for name in ["V4", "V4.1"]:
        r = final[name]
        print(
            f"{name:4s} | "
            f"F1={r['f1']:.4f} | "
            f"P={r['precision']:.4f} | "
            f"R={r['recall']:.4f} | "
            f"TP={r['tp']} FP={r['fp']} FN={r['fn']} | "
            f"CountMAE={r['count_mae']:.2f} | "
            f"conf={r['conf']:.2f} nms={r['nms']:.2f} "
            f"contain={r['containment']}"
        )

    winner = max(
        final,
        key=lambda name: final[name]["f1"],
    )

    print("\nBest ambulance F1:", winner)
    print(
        "Do not choose the final project detector from ambulance F1 alone; "
        "also compare the already-measured BMD F1 and BMD Count MAE."
    )
    print("=" * 110)


if __name__ == "__main__":
    main()
