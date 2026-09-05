import torch
from pathlib import Path
from torch.utils.data import DataLoader

from model_v4 import TrafficDetectorV4
from traffic_dataset_v4 import TrafficDatasetV4


# ==========================================================
# CONFIG
# ==========================================================

NUM_CLASSES = 15
IMAGE_SIZE = 448

SMALL_GRID_SIZE = 56
LARGE_GRID_SIZE = 28

NMS_IOU_THRESHOLD = 0.40
MATCH_IOU_THRESHOLD = 0.50

CONFIDENCE_THRESHOLDS = [
    0.10, 0.15, 0.20, 0.25, 0.30,
    0.35, 0.40, 0.45, 0.50, 0.55,
    0.60, 0.65, 0.70, 0.75, 0.80,
    0.85, 0.90
]

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
    "Ambulance"
]

BATCH_SIZE = 8

# Start with 4 because your optimized Windows DataLoader already
# worked well during V4 training. If Windows multiprocessing gives
# any issue, set this to 0 temporarily.
NUM_WORKERS = 4


# ==========================================================
# PATHS
# ==========================================================

MODEL_DIR = Path(__file__).resolve().parent

PROJECT_DIR = (
    MODEL_DIR.parent
)

MODEL_PATH = (
    MODEL_DIR
    / "traffic_detector_v4_best.pth"
)

BMD_IMAGE_DIR = (
    PROJECT_DIR
    / "dataset_v4"
    / "val"
    / "images"
)

BMD_LABEL_DIR = (
    PROJECT_DIR
    / "dataset_v4"
    / "val"
    / "labels"
)


def resolve_ambulance_validation_paths():

    candidates = [
        (
            PROJECT_DIR
            / "ambulance_v4"
            / "valid"
            / "images",

            PROJECT_DIR
            / "ambulance_v4"
            / "valid"
            / "labels"
        ),

        (
            PROJECT_DIR
            / "ambulance_v4"
            / "val"
            / "images",

            PROJECT_DIR
            / "ambulance_v4"
            / "val"
            / "labels"
        )
    ]

    for image_dir, label_dir in candidates:

        if (
            image_dir.exists()
            and
            label_dir.exists()
        ):

            return (
                image_dir,
                label_dir
            )

    return candidates[0]


(
    AMBULANCE_IMAGE_DIR,
    AMBULANCE_LABEL_DIR
) = resolve_ambulance_validation_paths()

# ==========================================================
# COLLATE
# ==========================================================

def detection_collate(batch):

    images = torch.stack(
        [
            sample[0]
            for sample in batch
        ],
        dim=0
    )

    boxes = [
        sample[1]
        for sample in batch
    ]

    categories = [
        sample[2]
        for sample in batch
    ]

    supervision = [
        sample[3]
        for sample in batch
    ]

    return (
        images,
        boxes,
        categories,
        supervision
    )


# ==========================================================
# IOU
#
# Box format:
# normalized [x1, y1, x2, y2]
# ==========================================================

def calculate_iou(
    box1,
    box2
):

    x1 = max(
        box1[0],
        box2[0]
    )

    y1 = max(
        box1[1],
        box2[1]
    )

    x2 = min(
        box1[2],
        box2[2]
    )

    y2 = min(
        box1[3],
        box2[3]
    )

    intersection_width = max(
        0.0,
        x2 - x1
    )

    intersection_height = max(
        0.0,
        y2 - y1
    )

    intersection_area = (
        intersection_width
        * intersection_height
    )

    box1_area = (
        max(
            0.0,
            box1[2] - box1[0]
        )
        *
        max(
            0.0,
            box1[3] - box1[1]
        )
    )

    box2_area = (
        max(
            0.0,
            box2[2] - box2[0]
        )
        *
        max(
            0.0,
            box2[3] - box2[1]
        )
    )

    union_area = (
        box1_area
        + box2_area
        - intersection_area
    )

    if union_area <= 0.0:
        return 0.0

    return (
        intersection_area
        / union_area
    )


# ==========================================================
# CLASS-AWARE NMS
#
# We combine both detection heads first and then apply NMS.
# Therefore duplicate predictions from 56x56 and 28x28 can
# suppress each other when they predict the same class.
# ==========================================================

def class_aware_nms(
    detections,
    iou_threshold=NMS_IOU_THRESHOLD
):

    if len(detections) == 0:
        return []

    detections = sorted(
        detections,
        key=lambda detection:
            detection["confidence"],
        reverse=True
    )

    kept = []

    while len(detections) > 0:

        best = detections.pop(0)

        kept.append(
            best
        )

        remaining = []

        for detection in detections:

            # Different classes do not suppress each other.
            if (
                detection["class_id"]
                !=
                best["class_id"]
            ):
                remaining.append(
                    detection
                )

                continue

            overlap = calculate_iou(
                best["box"],
                detection["box"]
            )

            if overlap < iou_threshold:

                remaining.append(
                    detection
                )

        detections = remaining

    return kept


# ==========================================================
# DECODE ONE V4 HEAD
#
# prediction shape:
# [20, grid, grid]
#
# Channel 0:
#     objectness logit
#
# Channels 1, 2:
#     tx, ty logits
#     sigmoid -> offset inside the grid cell
#
# Channels 3, 4:
#     width, height logits
#     sigmoid -> normalized image width/height
#
# Channels 5...19:
#     15-class logits
# ==========================================================

def decode_head(
    prediction,
    minimum_confidence
):

    if prediction.ndim != 3:

        raise ValueError(
            "decode_head expected "
            "[C,H,W], got "
            f"{tuple(prediction.shape)}"
        )

    (
        channels,
        grid_height,
        grid_width
    ) = prediction.shape

    expected_channels = (
        5 + NUM_CLASSES
    )

    if channels != expected_channels:

        raise ValueError(
            f"Expected {expected_channels} channels "
            f"but received {channels}."
        )

    if grid_height != grid_width:

        raise ValueError(
            "Expected square prediction grid, got "
            f"{grid_height}x{grid_width}."
        )

    grid_size = grid_height

    # ----------------------------------------------
    # OBJECTNESS
    # ----------------------------------------------

    objectness = torch.sigmoid(
        prediction[0]
    )

    # ----------------------------------------------
    # CLASS PROBABILITY
    # ----------------------------------------------

    class_probabilities = torch.softmax(
        prediction[5:],
        dim=0
    )

    (
        best_class_probability,
        best_class_id
    ) = torch.max(
        class_probabilities,
        dim=0
    )

    # Same confidence rule used by V3:
    # confidence = objectness * best class probability.
    confidence = (
        objectness
        * best_class_probability
    )

    positive_mask = (
        confidence
        >= minimum_confidence
    )

    (
        rows,
        columns
    ) = torch.where(
        positive_mask
    )

    if rows.numel() == 0:
        return []

    # ----------------------------------------------
    # BBOX
    # ----------------------------------------------

    tx = torch.sigmoid(
        prediction[
            1,
            rows,
            columns
        ]
    )

    ty = torch.sigmoid(
        prediction[
            2,
            rows,
            columns
        ]
    )

    width = torch.sigmoid(
        prediction[
            3,
            rows,
            columns
        ]
    )

    height = torch.sigmoid(
        prediction[
            4,
            rows,
            columns
        ]
    )

    center_x = (
        columns.float()
        + tx
    ) / grid_size

    center_y = (
        rows.float()
        + ty
    ) / grid_size

    x1 = torch.clamp(
        center_x - width / 2.0,
        min=0.0,
        max=1.0
    )

    y1 = torch.clamp(
        center_y - height / 2.0,
        min=0.0,
        max=1.0
    )

    x2 = torch.clamp(
        center_x + width / 2.0,
        min=0.0,
        max=1.0
    )

    y2 = torch.clamp(
        center_y + height / 2.0,
        min=0.0,
        max=1.0
    )

    selected_confidence = confidence[
        rows,
        columns
    ]

    selected_class_ids = best_class_id[
        rows,
        columns
    ]

    detections = []

    for index in range(
        rows.numel()
    ):

        box = (
            float(
                x1[index].item()
            ),
            float(
                y1[index].item()
            ),
            float(
                x2[index].item()
            ),
            float(
                y2[index].item()
            )
        )

        if (
            box[2] <= box[0]
            or
            box[3] <= box[1]
        ):
            continue

        detections.append(
            {
                "confidence":
                    float(
                        selected_confidence[
                            index
                        ].item()
                    ),

                "class_id":
                    int(
                        selected_class_ids[
                            index
                        ].item()
                    ),

                "box":
                    box
            }
        )

    return detections


# ==========================================================
# DECODE BOTH HEADS
# ==========================================================

def decode_multiscale_outputs(
    outputs,
    batch_index,
    minimum_confidence
):

    small_prediction = (
        outputs["small"][
            batch_index
        ]
        .detach()
        .float()
        .cpu()
    )

    large_prediction = (
        outputs["large"][
            batch_index
        ]
        .detach()
        .float()
        .cpu()
    )

    if (
        tuple(
            small_prediction.shape[-2:]
        )
        !=
        (
            SMALL_GRID_SIZE,
            SMALL_GRID_SIZE
        )
    ):

        raise ValueError(
            "Unexpected small-head shape: "
            f"{tuple(small_prediction.shape)}"
        )

    if (
        tuple(
            large_prediction.shape[-2:]
        )
        !=
        (
            LARGE_GRID_SIZE,
            LARGE_GRID_SIZE
        )
    ):

        raise ValueError(
            "Unexpected large-head shape: "
            f"{tuple(large_prediction.shape)}"
        )

    detections = []

    detections.extend(
        decode_head(
            small_prediction,
            minimum_confidence
        )
    )

    detections.extend(
        decode_head(
            large_prediction,
            minimum_confidence
        )
    )

    return class_aware_nms(
        detections,
        NMS_IOU_THRESHOLD
    )


# ==========================================================
# DATASET GROUND TRUTH
#
# TrafficDatasetV4 already applies the exact letterbox
# transformation used during training and returns boxes as:
#
# [x, y, width, height]
#
# in normalized letterboxed coordinates.
# ==========================================================

def build_ground_truth(
    boxes,
    categories
):

    ground_truth = []

    for box, category in zip(
        boxes,
        categories
    ):

        (
            x,
            y,
            width,
            height
        ) = [
            float(value)
            for value in box.tolist()
        ]

        x1 = max(
            0.0,
            min(
                1.0,
                x
            )
        )

        y1 = max(
            0.0,
            min(
                1.0,
                y
            )
        )

        x2 = max(
            0.0,
            min(
                1.0,
                x + width
            )
        )

        y2 = max(
            0.0,
            min(
                1.0,
                y + height
            )
        )

        if (
            x2 <= x1
            or
            y2 <= y1
        ):
            continue

        ground_truth.append(
            {
                "class_id":
                    int(
                        category.item()
                    ),

                "box":
                    (
                        x1,
                        y1,
                        x2,
                        y2
                    )
            }
        )

    return ground_truth


# ==========================================================
# MATCH PREDICTIONS TO GT
#
# A TP requires:
# 1. same class
# 2. IoU >= MATCH_IOU_THRESHOLD
# 3. each GT matched at most once
# ==========================================================

def match_detections(
    predictions,
    ground_truth
):

    predictions = sorted(
        predictions,
        key=lambda detection:
            detection["confidence"],
        reverse=True
    )

    matched_ground_truth = set()

    true_positive = 0
    false_positive = 0

    matched_ious = []

    for prediction in predictions:

        best_iou = 0.0
        best_gt_index = None

        for gt_index, gt in enumerate(
            ground_truth
        ):

            if (
                gt_index
                in matched_ground_truth
            ):
                continue

            if (
                prediction["class_id"]
                !=
                gt["class_id"]
            ):
                continue

            overlap = calculate_iou(
                prediction["box"],
                gt["box"]
            )

            if overlap > best_iou:

                best_iou = overlap
                best_gt_index = gt_index

        if (
            best_gt_index is not None
            and
            best_iou
            >= MATCH_IOU_THRESHOLD
        ):

            true_positive += 1

            matched_ground_truth.add(
                best_gt_index
            )

            matched_ious.append(
                best_iou
            )

        else:

            false_positive += 1

    false_negative = (
        len(ground_truth)
        - len(
            matched_ground_truth
        )
    )

    return (
        true_positive,
        false_positive,
        false_negative,
        matched_ious
    )


# ==========================================================
# RESULT HELPERS
# ==========================================================

def create_empty_result():

    return {
        "tp": 0,
        "fp": 0,
        "fn": 0,

        "predictions": 0,
        "ground_truth": 0,

        "absolute_count_error": 0.0,

        "matched_iou_sum": 0.0,
        "matched_iou_count": 0
    }


def calculate_metrics(
    result
):

    true_positive = result["tp"]
    false_positive = result["fp"]
    false_negative = result["fn"]

    precision = (
        true_positive
        /
        (
            true_positive
            + false_positive
        )
        if (
            true_positive
            + false_positive
        ) > 0
        else 0.0
    )

    recall = (
        true_positive
        /
        (
            true_positive
            + false_negative
        )
        if (
            true_positive
            + false_negative
        ) > 0
        else 0.0
    )

    f1_score = (
        2.0
        * precision
        * recall
        /
        (
            precision
            + recall
        )
        if (
            precision
            + recall
        ) > 0
        else 0.0
    )

    mean_matched_iou = (
        result["matched_iou_sum"]
        /
        result["matched_iou_count"]
        if (
            result["matched_iou_count"]
            > 0
        )
        else 0.0
    )

    return (
        precision,
        recall,
        f1_score,
        mean_matched_iou
    )


def update_result(
    result,
    predictions,
    ground_truth
):

    (
        true_positive,
        false_positive,
        false_negative,
        matched_ious
    ) = match_detections(
        predictions,
        ground_truth
    )

    result["tp"] += (
        true_positive
    )

    result["fp"] += (
        false_positive
    )

    result["fn"] += (
        false_negative
    )

    result[
        "predictions"
    ] += len(
        predictions
    )

    result[
        "ground_truth"
    ] += len(
        ground_truth
    )

    result[
        "absolute_count_error"
    ] += abs(
        len(predictions)
        - len(ground_truth)
    )

    result[
        "matched_iou_sum"
    ] += sum(
        matched_ious
    )

    result[
        "matched_iou_count"
    ] += len(
        matched_ious
    )


# ==========================================================
# DATA LOADER
# ==========================================================

def make_loader(
    image_dir,
    label_dir,
    device
):

    dataset = TrafficDatasetV4(
        image_dir,
        label_dir,
        image_size=IMAGE_SIZE,
        augment=False
    )

    loader_arguments = {
        "batch_size":
            BATCH_SIZE,

        "shuffle":
            False,

        "num_workers":
            NUM_WORKERS,

        "pin_memory":
            (
                device.type
                == "cuda"
            ),

        "collate_fn":
            detection_collate
    }

    if NUM_WORKERS > 0:

        loader_arguments[
            "persistent_workers"
        ] = True

        loader_arguments[
            "prefetch_factor"
        ] = 2

    loader = DataLoader(
        dataset,
        **loader_arguments
    )

    return (
        dataset,
        loader
    )


# ==========================================================
# MODEL LOADING
# ==========================================================

def load_best_model(
    device
):

    if not MODEL_PATH.exists():

        raise FileNotFoundError(
            "Best V4 model not found:\n"
            f"{MODEL_PATH}"
        )

    model = TrafficDetectorV4(
        num_classes=NUM_CLASSES
    ).to(
        device
    )

    loaded_object = torch.load(
        MODEL_PATH,
        map_location=device,
        weights_only=True
    )

    # Support both:
    # - a raw state_dict best model
    # - a checkpoint dictionary
    if (
        isinstance(
            loaded_object,
            dict
        )
        and
        "model_state_dict"
        in loaded_object
    ):

        state_dict = (
            loaded_object[
                "model_state_dict"
            ]
        )

    elif (
        isinstance(
            loaded_object,
            dict
        )
        and
        "model"
        in loaded_object
        and
        isinstance(
            loaded_object["model"],
            dict
        )
    ):

        state_dict = (
            loaded_object["model"]
        )

    else:

        state_dict = (
            loaded_object
        )

    model.load_state_dict(
        state_dict
    )

    model.eval()

    return model


# ==========================================================
# BMD EVALUATION
#
# BMD validation is fully annotated.
#
# Therefore:
# - overall precision is valid
# - overall recall is valid
# - F1 is valid
# - vehicle Count MAE is valid
# - per-class metrics are valid
# ==========================================================

def evaluate_bmd(
    model,
    device
):

    print(
        "\n"
        + "=" * 100
    )

    print(
        "BMD V4 VALIDATION "
        "(FULL SUPERVISION)"
    )

    print(
        "=" * 100
    )

    (
        dataset,
        loader
    ) = make_loader(
        BMD_IMAGE_DIR,
        BMD_LABEL_DIR,
        device
    )

    print(
        "Images:",
        len(dataset)
    )

    results = {
        threshold:
            create_empty_result()

        for threshold
        in CONFIDENCE_THRESHOLDS
    }

    cached_images = []

    minimum_threshold = min(
        CONFIDENCE_THRESHOLDS
    )

    processed = 0

    with torch.inference_mode():

        for (
            images,
            boxes_batch,
            categories_batch,
            _
        ) in loader:

            images = images.to(
                device,
                non_blocking=True
            )

            with torch.amp.autocast(
                device_type=device.type,
                dtype=torch.float16,
                enabled=(
                    device.type
                    == "cuda"
                )
            ):

                outputs = model(
                    images
                )

            for batch_index in range(
                images.shape[0]
            ):

                candidates = (
                    decode_multiscale_outputs(
                        outputs,
                        batch_index,
                        minimum_threshold
                    )
                )

                ground_truth = (
                    build_ground_truth(
                        boxes_batch[
                            batch_index
                        ],
                        categories_batch[
                            batch_index
                        ]
                    )
                )

                cached_images.append(
                    (
                        candidates,
                        ground_truth
                    )
                )

                for threshold in (
                    CONFIDENCE_THRESHOLDS
                ):

                    filtered_predictions = [
                        detection

                        for detection
                        in candidates

                        if (
                            detection[
                                "confidence"
                            ]
                            >= threshold
                        )
                    ]

                    update_result(
                        results[
                            threshold
                        ],
                        filtered_predictions,
                        ground_truth
                    )

                processed += 1

                if (
                    processed % 100
                    == 0
                ):

                    print(
                        f"Processed "
                        f"{processed}/"
                        f"{len(dataset)}"
                    )

    # ------------------------------------------------------
    # THRESHOLD TABLE
    # ------------------------------------------------------

    print(
        "\n"
        + "=" * 112
    )

    print(
        "BMD CONFIDENCE THRESHOLD SWEEP "
        f"(MATCH IoU={MATCH_IOU_THRESHOLD:.2f}, "
        f"NMS IoU={NMS_IOU_THRESHOLD:.2f})"
    )

    print(
        "=" * 112
    )

    print(
        f"{'Thr':<7}"
        f"{'Pred':<10}"
        f"{'GT':<10}"
        f"{'TP':<9}"
        f"{'FP':<10}"
        f"{'FN':<10}"
        f"{'Prec':<10}"
        f"{'Recall':<10}"
        f"{'F1':<10}"
        f"{'CountMAE':<11}"
        f"{'MeanTP-IoU':<12}"
    )

    print(
        "-" * 112
    )

    best_f1 = -1.0
    best_f1_threshold = None

    best_count_mae = float(
        "inf"
    )

    best_count_threshold = None

    for threshold in (
        CONFIDENCE_THRESHOLDS
    ):

        result = results[
            threshold
        ]

        (
            precision,
            recall,
            f1_score,
            mean_iou
        ) = calculate_metrics(
            result
        )

        count_mae = (
            result[
                "absolute_count_error"
            ]
            / len(dataset)
        )

        if f1_score > best_f1:

            best_f1 = (
                f1_score
            )

            best_f1_threshold = (
                threshold
            )

        if (
            count_mae
            < best_count_mae
        ):

            best_count_mae = (
                count_mae
            )

            best_count_threshold = (
                threshold
            )

        print(
            f"{threshold:<7.2f}"
            f"{result['predictions']:<10}"
            f"{result['ground_truth']:<10}"
            f"{result['tp']:<9}"
            f"{result['fp']:<10}"
            f"{result['fn']:<10}"
            f"{precision:<10.4f}"
            f"{recall:<10.4f}"
            f"{f1_score:<10.4f}"
            f"{count_mae:<11.2f}"
            f"{mean_iou:<12.4f}"
        )

    print(
        "\nBest BMD F1 threshold:",
        best_f1_threshold
    )

    print(
        "Best BMD F1:",
        round(
            best_f1,
            4
        )
    )

    print(
        "Best BMD count threshold:",
        best_count_threshold
    )

    print(
        "Lowest BMD Count MAE:",
        round(
            best_count_mae,
            2
        )
    )

    print_per_class_metrics(
        cached_images,
        best_f1_threshold
    )

    return {
        "best_f1":
            best_f1,

        "best_f1_threshold":
            best_f1_threshold,

        "best_count_mae":
            best_count_mae,

        "best_count_threshold":
            best_count_threshold
    }


# ==========================================================
# BMD PER-CLASS METRICS
# ==========================================================

def print_per_class_metrics(
    cached_images,
    threshold
):

    class_results = {
        class_id:
            create_empty_result()

        for class_id
        in range(14)
    }

    for (
        candidates,
        ground_truth
    ) in cached_images:

        for class_id in range(
            14
        ):

            class_predictions = [
                detection

                for detection
                in candidates

                if (
                    detection[
                        "confidence"
                    ]
                    >= threshold

                    and

                    detection[
                        "class_id"
                    ]
                    == class_id
                )
            ]

            class_ground_truth = [
                gt

                for gt
                in ground_truth

                if (
                    gt[
                        "class_id"
                    ]
                    == class_id
                )
            ]

            update_result(
                class_results[
                    class_id
                ],
                class_predictions,
                class_ground_truth
            )

    print(
        "\n"
        + "=" * 112
    )

    print(
        "BMD PER-CLASS METRICS "
        f"@ CONF={threshold:.2f}"
    )

    print(
        "=" * 112
    )

    print(
        f"{'ID':<4}"
        f"{'Class':<20}"
        f"{'GT':<9}"
        f"{'Pred':<9}"
        f"{'TP':<9}"
        f"{'FP':<9}"
        f"{'FN':<9}"
        f"{'Prec':<10}"
        f"{'Recall':<10}"
        f"{'F1':<10}"
        f"{'MeanIoU':<10}"
    )

    print(
        "-" * 112
    )

    for class_id in range(
        14
    ):

        result = class_results[
            class_id
        ]

        (
            precision,
            recall,
            f1_score,
            mean_iou
        ) = calculate_metrics(
            result
        )

        print(
            f"{class_id:<4}"
            f"{CLASS_NAMES[class_id]:<20}"
            f"{result['ground_truth']:<9}"
            f"{result['predictions']:<9}"
            f"{result['tp']:<9}"
            f"{result['fp']:<9}"
            f"{result['fn']:<9}"
            f"{precision:<10.4f}"
            f"{recall:<10.4f}"
            f"{f1_score:<10.4f}"
            f"{mean_iou:<10.4f}"
        )


# ==========================================================
# AMBULANCE EVALUATION
#
# IMPORTANT:
#
# ambulance_v4 is positive_only.
#
# We therefore evaluate ONLY class 14 here.
#
# Do not use these images to calculate overall BMD traffic
# precision because non-ambulance traffic may exist without
# compatible BMD labels.
# ==========================================================

def evaluate_ambulance(
    model,
    device
):

    print(
        "\n"
        + "=" * 100
    )

    print(
        "AMBULANCE VALIDATION "
        "(CLASS 14 ONLY)"
    )

    print(
        "=" * 100
    )

    (
        dataset,
        loader
    ) = make_loader(
        AMBULANCE_IMAGE_DIR,
        AMBULANCE_LABEL_DIR,
        device
    )

    print(
        "Images:",
        len(dataset)
    )

    results = {
        threshold:
            create_empty_result()

        for threshold
        in CONFIDENCE_THRESHOLDS
    }

    minimum_threshold = min(
        CONFIDENCE_THRESHOLDS
    )

    processed = 0

    with torch.inference_mode():

        for (
            images,
            boxes_batch,
            categories_batch,
            _
        ) in loader:

            images = images.to(
                device,
                non_blocking=True
            )

            with torch.amp.autocast(
                device_type=device.type,
                dtype=torch.float16,
                enabled=(
                    device.type
                    == "cuda"
                )
            ):

                outputs = model(
                    images
                )

            for batch_index in range(
                images.shape[0]
            ):

                all_candidates = (
                    decode_multiscale_outputs(
                        outputs,
                        batch_index,
                        minimum_threshold
                    )
                )

                ambulance_candidates = [
                    detection

                    for detection
                    in all_candidates

                    if (
                        detection[
                            "class_id"
                        ]
                        == 14
                    )
                ]

                all_ground_truth = (
                    build_ground_truth(
                        boxes_batch[
                            batch_index
                        ],
                        categories_batch[
                            batch_index
                        ]
                    )
                )

                ambulance_ground_truth = [
                    gt

                    for gt
                    in all_ground_truth

                    if (
                        gt[
                            "class_id"
                        ]
                        == 14
                    )
                ]

                for threshold in (
                    CONFIDENCE_THRESHOLDS
                ):

                    filtered_predictions = [
                        detection

                        for detection
                        in ambulance_candidates

                        if (
                            detection[
                                "confidence"
                            ]
                            >= threshold
                        )
                    ]

                    update_result(
                        results[
                            threshold
                        ],
                        filtered_predictions,
                        ambulance_ground_truth
                    )

                processed += 1

                if (
                    processed % 100
                    == 0
                ):

                    print(
                        f"Processed "
                        f"{processed}/"
                        f"{len(dataset)}"
                    )

    print(
        "\n"
        + "=" * 105
    )

    print(
        "AMBULANCE CLASS-14 "
        "CONFIDENCE THRESHOLD SWEEP"
    )

    print(
        "=" * 105
    )

    print(
        f"{'Thr':<7}"
        f"{'Pred':<10}"
        f"{'GT':<9}"
        f"{'TP':<9}"
        f"{'FP':<9}"
        f"{'FN':<9}"
        f"{'Prec':<10}"
        f"{'Recall':<10}"
        f"{'F1':<10}"
        f"{'CountMAE':<11}"
        f"{'MeanTP-IoU':<12}"
    )

    print(
        "-" * 105
    )

    best_f1 = -1.0
    best_threshold = None

    for threshold in (
        CONFIDENCE_THRESHOLDS
    ):

        result = results[
            threshold
        ]

        (
            precision,
            recall,
            f1_score,
            mean_iou
        ) = calculate_metrics(
            result
        )

        count_mae = (
            result[
                "absolute_count_error"
            ]
            / len(dataset)
        )

        if f1_score > best_f1:

            best_f1 = (
                f1_score
            )

            best_threshold = (
                threshold
            )

        print(
            f"{threshold:<7.2f}"
            f"{result['predictions']:<10}"
            f"{result['ground_truth']:<9}"
            f"{result['tp']:<9}"
            f"{result['fp']:<9}"
            f"{result['fn']:<9}"
            f"{precision:<10.4f}"
            f"{recall:<10.4f}"
            f"{f1_score:<10.4f}"
            f"{count_mae:<11.2f}"
            f"{mean_iou:<12.4f}"
        )

    print(
        "\nBest Ambulance threshold:",
        best_threshold
    )

    print(
        "Best Ambulance F1:",
        round(
            best_f1,
            4
        )
    )

    return {
        "best_f1":
            best_f1,

        "best_threshold":
            best_threshold
    }


# ==========================================================
# PATH VALIDATION
# ==========================================================

def validate_paths():

    required_paths = [
        (
            "Best V4 model",
            MODEL_PATH
        ),
        (
            "BMD validation images",
            BMD_IMAGE_DIR
        ),
        (
            "BMD validation labels",
            BMD_LABEL_DIR
        ),
        (
            "Ambulance validation images",
            AMBULANCE_IMAGE_DIR
        ),
        (
            "Ambulance validation labels",
            AMBULANCE_LABEL_DIR
        )
    ]

    missing = []

    for (
        name,
        path
    ) in required_paths:

        if not path.exists():

            missing.append(
                (
                    name,
                    path
                )
            )

    if len(missing) > 0:

        message = [
            "Missing required path(s):"
        ]

        for (
            name,
            path
        ) in missing:

            message.append(
                f"- {name}: {path}"
            )

        raise FileNotFoundError(
            "\n".join(
                message
            )
        )


# ==========================================================
# MAIN
# ==========================================================

def main():

    print(
        "=" * 100
    )

    print(
        "V4 TRAFFIC DETECTOR EVALUATION"
    )

    print(
        "=" * 100
    )

    print("MODEL DIR   :", MODEL_DIR)
    print("PROJECT DIR :", PROJECT_DIR)

    print("BMD images  :", BMD_IMAGE_DIR)
    print("BMD labels  :", BMD_LABEL_DIR)

    print("AMB images  :", AMBULANCE_IMAGE_DIR)
    print("AMB labels  :", AMBULANCE_LABEL_DIR)

    validate_paths()

    device = torch.device(
        "cuda"
        if torch.cuda.is_available()
        else "cpu"
    )

    print(
        "Device:",
        device
    )

    if device.type == "cuda":

        print(
            "GPU:",
            torch.cuda.get_device_name(
                0
            )
        )

        torch.backends.cudnn.benchmark = True

        torch.backends.cuda.matmul.allow_tf32 = (
            True
        )

        torch.backends.cudnn.allow_tf32 = (
            True
        )

        torch.set_float32_matmul_precision(
            "high"
        )

    print(
        "Model:",
        MODEL_PATH
    )

    print(
        "BMD val:",
        BMD_IMAGE_DIR
    )

    print(
        "Ambulance val:",
        AMBULANCE_IMAGE_DIR
    )

    print(
        "Match IoU:",
        MATCH_IOU_THRESHOLD
    )

    print(
        "NMS IoU:",
        NMS_IOU_THRESHOLD
    )

    print(
        "Classes:",
        NUM_CLASSES
    )

    model = load_best_model(
        device
    )

    print(
        "\n✅ Best V4 model loaded successfully."
    )

    bmd_results = evaluate_bmd(
        model,
        device
    )

    ambulance_results = (
        evaluate_ambulance(
            model,
            device
        )
    )

    print(
        "\n"
        + "=" * 100
    )

    print(
        "FINAL V4 SUMMARY"
    )

    print(
        "=" * 100
    )

    print(
        "BMD best F1       : "
        f"{bmd_results['best_f1']:.4f} "
        "@ conf "
        f"{bmd_results['best_f1_threshold']:.2f}"
    )

    print(
        "BMD best Count MAE: "
        f"{bmd_results['best_count_mae']:.2f} "
        "@ conf "
        f"{bmd_results['best_count_threshold']:.2f}"
    )

    print(
        "Ambulance best F1 : "
        f"{ambulance_results['best_f1']:.4f} "
        "@ conf "
        f"{ambulance_results['best_threshold']:.2f}"
    )

    print(
        "\nIMPORTANT:"
    )

    print(
        "- BMD metrics are evaluated on fully annotated "
        "traffic validation images."
    )

    print(
        "- Ambulance metrics are class-14-only because the "
        "ambulance source uses positive_only supervision."
    )

    print(
        "- MeanTP-IoU is the mean IoU of true-positive "
        "matched detections, not mAP."
    )

    print(
        "- Do NOT combine BMD F1 and Ambulance F1 into one "
        "'accuracy' percentage."
    )

    print(
        "=" * 100
    )


if __name__ == "__main__":

    main()
