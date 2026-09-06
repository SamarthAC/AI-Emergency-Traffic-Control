"""
inference_v4.py

Reusable inference wrapper for the final V4 traffic detector.

Final deployed checkpoint:
    traffic_detector_v4_best.pth

Post-processing:
- Normal traffic classes (0-13):
      confidence >= 0.80
      class-aware NMS IoU = 0.40
- Ambulance class (14):
      confidence >= 0.96
      NMS IoU = 0.20
      directional containment = 0.80

The CNN returns normalized boxes in the model's 448x448 letterboxed space.
This wrapper maps them back to original-image pixel coordinates.
"""

from pathlib import Path
from collections import Counter
import argparse
import json

import torch
from PIL import Image, ImageDraw

from model_v4 import TrafficDetectorV4


# ==========================================================
# CONFIG
# ==========================================================

MODEL_DIR = Path(__file__).resolve().parent
MODEL_PATH = MODEL_DIR / "traffic_detector_v4_best.pth"

NUM_CLASSES = 15
IMAGE_SIZE = 448

# General traffic
TRAFFIC_CONFIDENCE = 0.65
TRAFFIC_NMS_IOU = 0.40

# Ambulance
AMBULANCE_CLASS_ID = 14
AMBULANCE_CONFIDENCE = 0.70
AMBULANCE_NMS_IOU = 0.20
AMBULANCE_CONTAINMENT = 0.80

# Decode low enough to preserve both traffic and ambulance candidates.
RAW_DECODE_CONFIDENCE = min(
    TRAFFIC_CONFIDENCE,
    AMBULANCE_CONFIDENCE,
)

CLASS_NAMES = [
    "Hatchback",
    "Sedan",
    "SUV",
    "MUV",
    "Bus",
    "Truck",
    "Three-wheeler",
    "Two-wheeler",
    "LCV",
    "Mini-bus",
    "Tempo-traveller",
    "Bicycle",
    "Van",
    "Other",
    "Ambulance",
]


# ==========================================================
# MODEL LOADING
# ==========================================================

def _extract_state_dict(loaded_object):
    if (
        isinstance(loaded_object, dict)
        and "model_state_dict" in loaded_object
    ):
        return loaded_object["model_state_dict"]

    if (
        isinstance(loaded_object, dict)
        and "model" in loaded_object
        and isinstance(loaded_object["model"], dict)
    ):
        return loaded_object["model"]

    return loaded_object


def load_model(device):
    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            f"V4 model not found:\n{MODEL_PATH}"
        )

    model = TrafficDetectorV4(
        num_classes=NUM_CLASSES
    ).to(device)

    loaded_object = torch.load(
        MODEL_PATH,
        map_location=device,
        weights_only=True,
    )

    model.load_state_dict(
        _extract_state_dict(loaded_object)
    )

    model.eval()
    return model


# ==========================================================
# LETTERBOX PREPROCESSING
# ==========================================================

def letterbox_image(image, size=IMAGE_SIZE):
    """
    Resize while preserving aspect ratio and pad to size x size.

    Returns:
        tensor: [3,size,size], float32 [0,1]
        meta: values required to map model boxes back to original pixels
    """
    image = image.convert("RGB")

    original_width, original_height = image.size

    scale = min(
        size / original_width,
        size / original_height,
    )

    resized_width = max(
        1,
        int(round(original_width * scale)),
    )
    resized_height = max(
        1,
        int(round(original_height * scale)),
    )

    resized = image.resize(
        (resized_width, resized_height),
        Image.BILINEAR,
    )

    pad_left = (size - resized_width) // 2
    pad_top = (size - resized_height) // 2

    canvas = Image.new(
        "RGB",
        (size, size),
        (114, 114, 114),
    )

    canvas.paste(
        resized,
        (pad_left, pad_top),
    )

    # Avoid torchvision dependency.
    byte_tensor = torch.frombuffer(
        bytearray(canvas.tobytes()),
        dtype=torch.uint8,
    )

    tensor = (
        byte_tensor
        .view(size, size, 3)
        .permute(2, 0, 1)
        .contiguous()
        .float()
        / 255.0
    )

    meta = {
        "original_width": original_width,
        "original_height": original_height,
        "scale": scale,
        "pad_left": pad_left,
        "pad_top": pad_top,
        "input_size": size,
    }

    return tensor, meta


# ==========================================================
# V4 DECODER
# Same encoding used by evaluate_v4.py.
# ==========================================================

def decode_head(prediction, minimum_confidence):
    if prediction.ndim != 3:
        raise ValueError(
            "decode_head expected [C,H,W], got "
            f"{tuple(prediction.shape)}"
        )

    channels, grid_height, grid_width = prediction.shape

    expected_channels = 5 + NUM_CLASSES

    if channels != expected_channels:
        raise ValueError(
            f"Expected {expected_channels} channels, "
            f"received {channels}."
        )

    if grid_height != grid_width:
        raise ValueError(
            f"Expected square grid, got "
            f"{grid_height}x{grid_width}."
        )

    grid_size = grid_height

    objectness = torch.sigmoid(
        prediction[0]
    )

    class_probabilities = torch.softmax(
        prediction[5:],
        dim=0,
    )

    (
        best_class_probability,
        best_class_id,
    ) = torch.max(
        class_probabilities,
        dim=0,
    )

    confidence = (
        objectness
        * best_class_probability
    )

    positive_mask = (
        confidence >= minimum_confidence
    )

    rows, columns = torch.where(
        positive_mask
    )

    if rows.numel() == 0:
        return []

    tx = torch.sigmoid(
        prediction[
            1,
            rows,
            columns,
        ]
    )

    ty = torch.sigmoid(
        prediction[
            2,
            rows,
            columns,
        ]
    )

    width = torch.sigmoid(
        prediction[
            3,
            rows,
            columns,
        ]
    )

    height = torch.sigmoid(
        prediction[
            4,
            rows,
            columns,
        ]
    )

    center_x = (
        columns.float() + tx
    ) / grid_size

    center_y = (
        rows.float() + ty
    ) / grid_size

    x1 = torch.clamp(
        center_x - width / 2.0,
        0.0,
        1.0,
    )
    y1 = torch.clamp(
        center_y - height / 2.0,
        0.0,
        1.0,
    )
    x2 = torch.clamp(
        center_x + width / 2.0,
        0.0,
        1.0,
    )
    y2 = torch.clamp(
        center_y + height / 2.0,
        0.0,
        1.0,
    )

    selected_confidence = confidence[
        rows,
        columns,
    ]

    selected_class_ids = best_class_id[
        rows,
        columns,
    ]

    detections = []

    for index in range(rows.numel()):
        box = (
            float(x1[index].item()),
            float(y1[index].item()),
            float(x2[index].item()),
            float(y2[index].item()),
        )

        if (
            box[2] <= box[0]
            or box[3] <= box[1]
        ):
            continue

        detections.append(
            {
                "confidence": float(
                    selected_confidence[index].item()
                ),
                "class_id": int(
                    selected_class_ids[index].item()
                ),
                "box": box,
            }
        )

    return detections


def decode_outputs(outputs):
    detections = []

    for head_name in ("small", "large"):
        prediction = (
            outputs[head_name][0]
            .detach()
            .float()
            .cpu()
        )

        detections.extend(
            decode_head(
                prediction,
                RAW_DECODE_CONFIDENCE,
            )
        )

    return detections


# ==========================================================
# BOX GEOMETRY
# ==========================================================

def box_area(box):
    return (
        max(0.0, box[2] - box[0])
        * max(0.0, box[3] - box[1])
    )


def intersection_area(a, b):
    x1 = max(a[0], b[0])
    y1 = max(a[1], b[1])
    x2 = min(a[2], b[2])
    y2 = min(a[3], b[3])

    return (
        max(0.0, x2 - x1)
        * max(0.0, y2 - y1)
    )


def calculate_iou(a, b):
    intersection = intersection_area(
        a,
        b,
    )

    union = (
        box_area(a)
        + box_area(b)
        - intersection
    )

    if union <= 0.0:
        return 0.0

    return intersection / union


def candidate_containment(
    kept_box,
    candidate_box,
):
    candidate_area = box_area(
        candidate_box
    )

    if candidate_area <= 0.0:
        return 0.0

    return (
        intersection_area(
            kept_box,
            candidate_box,
        )
        / candidate_area
    )


# ==========================================================
# POST-PROCESSING
# ==========================================================

def class_aware_nms(
    detections,
    iou_threshold,
):
    detections = sorted(
        detections,
        key=lambda detection:
            detection["confidence"],
        reverse=True,
    )

    kept = []

    while detections:
        best = detections.pop(0)
        kept.append(best)

        remaining = []

        for detection in detections:
            if (
                detection["class_id"]
                != best["class_id"]
            ):
                remaining.append(
                    detection
                )
                continue

            if (
                calculate_iou(
                    best["box"],
                    detection["box"],
                )
                < iou_threshold
            ):
                remaining.append(
                    detection
                )

        detections = remaining

    return kept


def ambulance_postprocess(detections):
    detections = [
        detection
        for detection in detections
        if (
            detection["class_id"]
            == AMBULANCE_CLASS_ID
            and detection["confidence"]
            >= AMBULANCE_CONFIDENCE
        )
    ]

    detections.sort(
        key=lambda detection:
            detection["confidence"],
        reverse=True,
    )

    kept = []

    while detections:
        best = detections.pop(0)
        kept.append(best)

        remaining = []

        for candidate in detections:

            if (
                calculate_iou(
                    best["box"],
                    candidate["box"],
                )
                >= AMBULANCE_NMS_IOU
            ):
                continue

            contained = candidate_containment(
                best["box"],
                candidate["box"],
            )

            if (
                contained
                >= AMBULANCE_CONTAINMENT
            ):
                continue

            remaining.append(
                candidate
            )

        detections = remaining

    return kept


def postprocess(raw_detections):
    traffic = [
        detection
        for detection in raw_detections
        if (
            detection["class_id"]
            != AMBULANCE_CLASS_ID
            and detection["confidence"]
            >= TRAFFIC_CONFIDENCE
        )
    ]

    traffic = class_aware_nms(
        traffic,
        TRAFFIC_NMS_IOU,
    )

    ambulance = ambulance_postprocess(
        raw_detections
    )

    combined = traffic + ambulance

    combined.sort(
        key=lambda detection:
            detection["confidence"],
        reverse=True,
    )

    return combined


# ==========================================================
# COORDINATE CONVERSION
# ==========================================================

def normalized_to_original_pixels(
    box,
    meta,
):
    """
    Model box:
        normalized xyxy in 448x448 letterboxed coordinates

    Output:
        xyxy in original-image pixel coordinates
    """
    size = meta["input_size"]

    x1_lb = box[0] * size
    y1_lb = box[1] * size
    x2_lb = box[2] * size
    y2_lb = box[3] * size

    scale = meta["scale"]

    x1 = (
        x1_lb - meta["pad_left"]
    ) / scale
    y1 = (
        y1_lb - meta["pad_top"]
    ) / scale
    x2 = (
        x2_lb - meta["pad_left"]
    ) / scale
    y2 = (
        y2_lb - meta["pad_top"]
    ) / scale

    original_width = meta[
        "original_width"
    ]
    original_height = meta[
        "original_height"
    ]

    x1 = max(
        0.0,
        min(
            float(original_width),
            x1,
        ),
    )
    y1 = max(
        0.0,
        min(
            float(original_height),
            y1,
        ),
    )
    x2 = max(
        0.0,
        min(
            float(original_width),
            x2,
        ),
    )
    y2 = max(
        0.0,
        min(
            float(original_height),
            y2,
        ),
    )

    return [
        round(x1, 1),
        round(y1, 1),
        round(x2, 1),
        round(y2, 1),
    ]


# ==========================================================
# REUSABLE INFERENCE CLASS
# ==========================================================

class TrafficInferenceV4:

    def __init__(self, device=None):
        if device is None:
            device = (
                "cuda"
                if torch.cuda.is_available()
                else "cpu"
            )

        self.device = torch.device(
            device
        )

        if self.device.type == "cuda":
            torch.backends.cudnn.benchmark = True
            torch.backends.cuda.matmul.allow_tf32 = True
            torch.backends.cudnn.allow_tf32 = True
            torch.set_float32_matmul_precision(
                "high"
            )

        self.model = load_model(
            self.device
        )

    @torch.inference_mode()
    def predict(self, image_input):
        """
        image_input:
            str / Path / PIL.Image.Image

        Returns a JSON-serializable dictionary.
        """

        if isinstance(
            image_input,
            (str, Path),
        ):
            image_path = Path(
                image_input
            )

            if not image_path.exists():
                raise FileNotFoundError(
                    f"Image not found:\n"
                    f"{image_path}"
                )

            image = Image.open(
                image_path
            ).convert("RGB")

            image_name = (
                image_path.name
            )

        elif isinstance(
            image_input,
            Image.Image,
        ):
            image = (
                image_input
                .convert("RGB")
            )

            image_name = None

        else:
            raise TypeError(
                "image_input must be a path "
                "or PIL.Image.Image"
            )

        tensor, meta = letterbox_image(
            image
        )

        batch = (
            tensor
            .unsqueeze(0)
            .to(
                self.device,
                non_blocking=True,
            )
        )

        if self.device.type == "cuda":
            with torch.amp.autocast(
                device_type="cuda"
            ):
                outputs = self.model(
                    batch
                )
        else:
            outputs = self.model(
                batch
            )

        raw_detections = decode_outputs(
            outputs
        )

        detections = postprocess(
            raw_detections
        )

        result_detections = []

        counts = Counter()

        for detection in detections:
            class_id = detection[
                "class_id"
            ]

            class_name = CLASS_NAMES[
                class_id
            ]

            counts[class_name] += 1

            result_detections.append(
                {
                    "class_id":
                        class_id,
                    "class_name":
                        class_name,
                    "confidence":
                        round(
                            detection[
                                "confidence"
                            ],
                            4,
                        ),
                    "box_normalized":
                        [
                            round(
                                float(value),
                                6,
                            )
                            for value
                            in detection[
                                "box"
                            ]
                        ],
                    "box_pixels":
                        normalized_to_original_pixels(
                            detection[
                                "box"
                            ],
                            meta,
                        ),
                }
            )

        ambulance_detections = [
            detection
            for detection
            in result_detections
            if (
                detection[
                    "class_id"
                ]
                == AMBULANCE_CLASS_ID
            )
        ]

        vehicle_count = len(
            result_detections
        )

        non_ambulance_vehicle_count = (
            vehicle_count
            - len(
                ambulance_detections
            )
        )

        return {
            "image":
                image_name,
            "image_width":
                image.width,
            "image_height":
                image.height,
            "device":
                str(
                    self.device
                ),
            "vehicle_count":
                vehicle_count,
            "non_ambulance_vehicle_count":
                non_ambulance_vehicle_count,
            "ambulance_detected":
                len(
                    ambulance_detections
                ) > 0,
            "ambulance_count":
                len(
                    ambulance_detections
                ),
            "highest_ambulance_confidence":
                (
                    max(
                        detection[
                            "confidence"
                        ]
                        for detection
                        in ambulance_detections
                    )
                    if ambulance_detections
                    else None
                ),
            "class_counts":
                dict(
                    sorted(
                        counts.items()
                    )
                ),
            "detections":
                result_detections,
        }


# ==========================================================
# OPTIONAL VISUALIZATION
# ==========================================================

def save_annotated_image(
    image_path,
    result,
    output_path,
):
    image = Image.open(
        image_path
    ).convert("RGB")

    draw = ImageDraw.Draw(
        image
    )

    for detection in result[
        "detections"
    ]:
        x1, y1, x2, y2 = detection[
            "box_pixels"
        ]

        draw.rectangle(
            [x1, y1, x2, y2],
            width=3,
        )

        label = (
            f"{detection['class_name']} "
            f"{detection['confidence']:.2f}"
        )

        draw.text(
            (x1 + 3, y1 + 3),
            label,
        )

    image.save(
        output_path
    )


# ==========================================================
# CLI
# ==========================================================

def print_summary(result):
    print(
        "\n"
        + "=" * 70
    )
    print(
        "V4 TRAFFIC INFERENCE"
    )
    print(
        "=" * 70
    )

    print(
        "Device:",
        result["device"]
    )

    print(
        "Image:",
        result["image"]
    )

    print(
        "Size:",
        f"{result['image_width']}x"
        f"{result['image_height']}"
    )

    print(
        "\nDetections:"
    )

    if not result["detections"]:
        print(
            "  No detections above "
            "deployment thresholds."
        )

    for detection in result[
        "detections"
    ]:
        print(
            f"  "
            f"{detection['class_name']:<18} "
            f"conf="
            f"{detection['confidence']:.4f} "
            f"box="
            f"{detection['box_pixels']}"
        )

    print(
        "\nTotal vehicles:",
        result[
            "vehicle_count"
        ]
    )

    print(
        "Ambulance detected:",
        result[
            "ambulance_detected"
        ]
    )

    if result[
        "ambulance_detected"
    ]:
        print(
            "Ambulance count:",
            result[
                "ambulance_count"
            ]
        )

        print(
            "Highest ambulance confidence:",
            result[
                "highest_ambulance_confidence"
            ]
        )

    print(
        "\nClass counts:"
    )

    if not result[
        "class_counts"
    ]:
        print(
            "  {}"
        )
    else:
        for class_name, count in result[
            "class_counts"
        ].items():
            print(
                f"  {class_name:<18}: "
                f"{count}"
            )

    print(
        "=" * 70
    )


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Run final V4 traffic detector "
            "on one image."
        )
    )

    parser.add_argument(
        "image",
        type=str,
        help="Path to input image",
    )

    parser.add_argument(
        "--save",
        type=str,
        default=None,
        help=(
            "Optional path for an "
            "annotated output image"
        ),
    )

    parser.add_argument(
        "--json",
        type=str,
        default=None,
        help=(
            "Optional path to save "
            "structured JSON output"
        ),
    )

    args = parser.parse_args()

    detector = TrafficInferenceV4()

    result = detector.predict(
        args.image
    )

    print_summary(
        result
    )

    if args.save is not None:
        save_annotated_image(
            args.image,
            result,
            args.save,
        )

        print(
            "Annotated image saved:",
            args.save
        )

    if args.json is not None:
        json_path = Path(
            args.json
        )

        json_path.write_text(
            json.dumps(
                result,
                indent=2,
            ),
            encoding="utf-8",
        )

        print(
            "JSON saved:",
            json_path
        )


if __name__ == "__main__":
    main()
