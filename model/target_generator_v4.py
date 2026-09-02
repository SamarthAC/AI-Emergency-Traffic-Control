import torch


# ==========================================================
# V4 SETTINGS
# ==========================================================

IMAGE_SIZE = 448

SMALL_GRID_SIZE = 56
LARGE_GRID_SIZE = 28

SIZE_THRESHOLD_PX = 32
SIZE_THRESHOLD_AREA = SIZE_THRESHOLD_PX ** 2

# 14 BMD classes + Ambulance
NUM_CLASSES = 15


# ==========================================================
# V4 TARGET GENERATOR
# ==========================================================

def create_target_grid_v4(
    boxes,
    categories,
    grid_size=28,
    num_classes=NUM_CLASSES
):
    """
    boxes:
        Tensor [N, 4]

        Normalized letterboxed coordinates:
        [x, y, width, height]

    categories:
        Tensor [N]

    Output:
        target:
        [5 + num_classes, grid_size, grid_size]

    Channels:
        0       -> objectness
        1       -> center-x offset inside cell
        2       -> center-y offset inside cell
        3       -> normalized width
        4       -> normalized height
        5...    -> class one-hot
    """

    target = torch.zeros(
        (
            5 + num_classes,
            grid_size,
            grid_size
        ),
        dtype=torch.float32
    )

    # Used when multiple objects land
    # inside the same grid cell.
    #
    # Larger object is retained.
    assigned_area = torch.zeros(
        (
            grid_size,
            grid_size
        ),
        dtype=torch.float32
    )

    collision_count = 0

    # ======================================================
    # ENCODE OBJECTS
    # ======================================================

    for box, category in zip(
        boxes,
        categories
    ):

        x, y, width, height = (
            box.tolist()
        )

        class_id = int(
            category.item()
        )

        # --------------------------------------------------
        # VALIDATION
        # --------------------------------------------------

        if (
            class_id < 0
            or class_id >= num_classes
        ):
            continue

        if (
            width <= 0
            or height <= 0
        ):
            continue

        # --------------------------------------------------
        # TOP-LEFT -> CENTER
        # --------------------------------------------------

        center_x = (
            x + width / 2.0
        )

        center_y = (
            y + height / 2.0
        )

        # Numerical safety
        center_x = min(
            max(
                center_x,
                0.0
            ),
            1.0 - 1e-6
        )

        center_y = min(
            max(
                center_y,
                0.0
            ),
            1.0 - 1e-6
        )

        # --------------------------------------------------
        # GRID POSITION
        # --------------------------------------------------

        grid_x_float = (
            center_x
            * grid_size
        )

        grid_y_float = (
            center_y
            * grid_size
        )

        grid_x = int(
            grid_x_float
        )

        grid_y = int(
            grid_y_float
        )

        # --------------------------------------------------
        # OFFSET INSIDE CELL
        # --------------------------------------------------

        offset_x = (
            grid_x_float
            - grid_x
        )

        offset_y = (
            grid_y_float
            - grid_y
        )

        # --------------------------------------------------
        # COLLISION HANDLING
        # --------------------------------------------------

        area = (
            width
            * height
        )

        if (
            target[
                0,
                grid_y,
                grid_x
            ]
            == 1
        ):

            collision_count += 1

            existing_area = (
                assigned_area[
                    grid_y,
                    grid_x
                ]
            )

            # Keep existing object
            # if it is larger.
            if area <= existing_area:
                continue

            # New object is larger.
            # Clear old target first.
            target[
                :,
                grid_y,
                grid_x
            ] = 0.0

        assigned_area[
            grid_y,
            grid_x
        ] = area

        # --------------------------------------------------
        # OBJECTNESS
        # --------------------------------------------------

        target[
            0,
            grid_y,
            grid_x
        ] = 1.0

        # --------------------------------------------------
        # BOUNDING BOX
        # --------------------------------------------------

        target[
            1,
            grid_y,
            grid_x
        ] = offset_x

        target[
            2,
            grid_y,
            grid_x
        ] = offset_y

        target[
            3,
            grid_y,
            grid_x
        ] = width

        target[
            4,
            grid_y,
            grid_x
        ] = height

        # --------------------------------------------------
        # CLASS
        # --------------------------------------------------

        target[
            5 + class_id,
            grid_y,
            grid_x
        ] = 1.0

    return (
        target,
        collision_count
    )


# ==========================================================
# DECODE GROUND-TRUTH TARGET
# ==========================================================

def decode_target_grid_v4(
    target,
    grid_size=28
):
    """
    Converts encoded target back into:

    [x, y, width, height, class_id]

    Coordinates are normalized.
    """

    decoded = []

    for grid_y in range(
        grid_size
    ):

        for grid_x in range(
            grid_size
        ):

            objectness = target[
                0,
                grid_y,
                grid_x
            ].item()

            if objectness < 0.5:
                continue

            offset_x = target[
                1,
                grid_y,
                grid_x
            ].item()

            offset_y = target[
                2,
                grid_y,
                grid_x
            ].item()

            width = target[
                3,
                grid_y,
                grid_x
            ].item()

            height = target[
                4,
                grid_y,
                grid_x
            ].item()

            # --------------------------------------------------
            # GRID -> NORMALIZED CENTER
            # --------------------------------------------------

            center_x = (
                grid_x
                + offset_x
            ) / grid_size

            center_y = (
                grid_y
                + offset_y
            ) / grid_size

            # --------------------------------------------------
            # CENTER -> TOP LEFT
            # --------------------------------------------------

            x = (
                center_x
                - width / 2.0
            )

            y = (
                center_y
                - height / 2.0
            )

            # --------------------------------------------------
            # CLASS
            # --------------------------------------------------

            class_scores = target[
                5:,
                grid_y,
                grid_x
            ]

            class_id = int(
                torch.argmax(
                    class_scores
                ).item()
            )

            decoded.append(
                [
                    x,
                    y,
                    width,
                    height,
                    class_id
                ]
            )

    return decoded


# ==========================================================
# IoU
# ==========================================================

def box_iou_xywh(
    box1,
    box2
):
    """
    box format:

    [x, y, width, height]

    x and y are top-left coordinates.
    """

    x1, y1, w1, h1 = box1
    x2, y2, w2, h2 = box2

    box1_x2 = (
        x1 + w1
    )

    box1_y2 = (
        y1 + h1
    )

    box2_x2 = (
        x2 + w2
    )

    box2_y2 = (
        y2 + h2
    )

    intersection_x1 = max(
        x1,
        x2
    )

    intersection_y1 = max(
        y1,
        y2
    )

    intersection_x2 = min(
        box1_x2,
        box2_x2
    )

    intersection_y2 = min(
        box1_y2,
        box2_y2
    )

    intersection_width = max(
        0.0,
        intersection_x2
        - intersection_x1
    )

    intersection_height = max(
        0.0,
        intersection_y2
        - intersection_y1
    )

    intersection_area = (
        intersection_width
        * intersection_height
    )

    area1 = (
        w1 * h1
    )

    area2 = (
        w2 * h2
    )

    union = (
        area1
        + area2
        - intersection_area
    )

    if union <= 0:
        return 0.0

    return (
        intersection_area
        / union
    )


# ==========================================================
# MULTI-SCALE TARGET GENERATOR
# ==========================================================

def create_multiscale_targets_v4(
    boxes,
    categories,
    supervision="full",
    num_classes=NUM_CLASSES,
    image_size=IMAGE_SIZE,
    size_threshold_px=SIZE_THRESHOLD_PX
):
    """
    Creates targets for two detection heads.

    SMALL HEAD:
        objects with area < threshold^2
        -> 56x56

    LARGE HEAD:
        objects with area >= threshold^2
        -> 28x28

    supervision:

        "full"
            Used for BMD images.

            Positive cells:
                objectness supervised

            Empty cells:
                background/no-object supervised

        "positive_only"
            Used for ambulance-source images.

            Only known ambulance-positive cells
            receive objectness supervision.

            All other cells are ignored for
            objectness loss because those images
            may contain unlabeled traffic objects.
    """

    # ======================================================
    # VALIDATE SUPERVISION
    # ======================================================

    if supervision not in {
        "full",
        "positive_only"
    }:

        raise ValueError(
            f"Unknown supervision mode: "
            f"{supervision}"
        )

    # ======================================================
    # SPLIT OBJECTS BY SIZE
    # ======================================================

    small_boxes = []
    small_categories = []

    large_boxes = []
    large_categories = []

    threshold_area = (
        size_threshold_px
        ** 2
    )

    for box, category in zip(
        boxes,
        categories
    ):

        x, y, w, h = (
            box.tolist()
        )

        class_id = int(
            category.item()
        )

        # Skip invalid class IDs
        if (
            class_id < 0
            or class_id >= num_classes
        ):
            continue

        # Skip invalid dimensions
        if (
            w <= 0
            or h <= 0
        ):
            continue

        pixel_width = (
            w * image_size
        )

        pixel_height = (
            h * image_size
        )

        pixel_area = (
            pixel_width
            * pixel_height
        )

        # --------------------------------------------------
        # SMALL
        # --------------------------------------------------

        if (
            pixel_area
            < threshold_area
        ):

            small_boxes.append(
                [
                    x,
                    y,
                    w,
                    h
                ]
            )

            small_categories.append(
                class_id
            )

        # --------------------------------------------------
        # LARGE
        # --------------------------------------------------

        else:

            large_boxes.append(
                [
                    x,
                    y,
                    w,
                    h
                ]
            )

            large_categories.append(
                class_id
            )

    # ======================================================
    # SMALL LIST -> TENSOR
    # ======================================================

    if small_boxes:

        small_boxes = torch.tensor(
            small_boxes,
            dtype=torch.float32
        )

        small_categories = torch.tensor(
            small_categories,
            dtype=torch.long
        )

    else:

        small_boxes = torch.empty(
            (
                0,
                4
            ),
            dtype=torch.float32
        )

        small_categories = torch.empty(
            (0,),
            dtype=torch.long
        )

    # ======================================================
    # LARGE LIST -> TENSOR
    # ======================================================

    if large_boxes:

        large_boxes = torch.tensor(
            large_boxes,
            dtype=torch.float32
        )

        large_categories = torch.tensor(
            large_categories,
            dtype=torch.long
        )

    else:

        large_boxes = torch.empty(
            (
                0,
                4
            ),
            dtype=torch.float32
        )

        large_categories = torch.empty(
            (0,),
            dtype=torch.long
        )

    # ======================================================
    # CREATE SMALL TARGET
    # ======================================================

    (
        small_target,
        small_collisions
    ) = create_target_grid_v4(
        small_boxes,
        small_categories,
        grid_size=SMALL_GRID_SIZE,
        num_classes=num_classes
    )

    # ======================================================
    # CREATE LARGE TARGET
    # ======================================================

    (
        large_target,
        large_collisions
    ) = create_target_grid_v4(
        large_boxes,
        large_categories,
        grid_size=LARGE_GRID_SIZE,
        num_classes=num_classes
    )

    # ======================================================
    # OBJECTNESS SUPERVISION MASK
    # ======================================================
    #
    # Mask meaning:
    #
    # 1 -> calculate objectness loss
    # 0 -> completely ignore cell
    #
    # BBox and classification losses already use
    # positive target cells only.
    # ======================================================

    if supervision == "full":

        # --------------------------------------------------
        # BMD
        # --------------------------------------------------
        #
        # Every grid cell is trustworthy because
        # the image is fully annotated.
        # --------------------------------------------------

        small_objectness_mask = (
            torch.ones(
                (
                    SMALL_GRID_SIZE,
                    SMALL_GRID_SIZE
                ),
                dtype=torch.float32
            )
        )

        large_objectness_mask = (
            torch.ones(
                (
                    LARGE_GRID_SIZE,
                    LARGE_GRID_SIZE
                ),
                dtype=torch.float32
            )
        )

    else:

        # --------------------------------------------------
        # AMBULANCE SOURCE
        # --------------------------------------------------
        #
        # Only known ambulance cells are trustworthy.
        #
        # Other locations might contain cars,
        # bikes, buses, trucks, etc. which are
        # not mapped to our BMD class taxonomy.
        # --------------------------------------------------

        small_objectness_mask = (
            (
                small_target[0]
                > 0.5
            )
            .float()
        )

        large_objectness_mask = (
            (
                large_target[0]
                > 0.5
            )
            .float()
        )

    # ======================================================
    # RETURN
    # ======================================================

    return {

        "small_target":
            small_target,

        "large_target":
            large_target,

        "small_objectness_mask":
            small_objectness_mask,

        "large_objectness_mask":
            large_objectness_mask,

        "small_boxes":
            small_boxes,

        "large_boxes":
            large_boxes,

        "small_categories":
            small_categories,

        "large_categories":
            large_categories,

        "small_collisions":
            small_collisions,

        "large_collisions":
            large_collisions,

        "supervision":
            supervision
    }


# ==========================================================
# BASIC TEST
# ==========================================================

if __name__ == "__main__":

    print(
        "=" * 70
    )

    print(
        "V4 TARGET GENERATOR TEST"
    )

    print(
        "=" * 70
    )

    # ======================================================
    # TEST OBJECTS
    # ======================================================

    boxes = torch.tensor(
        [
            [
                0.10,
                0.20,
                0.04,
                0.04
            ],
            [
                0.55,
                0.45,
                0.20,
                0.18
            ],
            [
                0.75,
                0.65,
                0.08,
                0.12
            ],
            [
                0.30,
                0.30,
                0.25,
                0.15
            ]
        ],
        dtype=torch.float32
    )

    categories = torch.tensor(
        [
            7,
            4,
            6,
            14
        ],
        dtype=torch.long
    )

    # ======================================================
    # FULL SUPERVISION TEST
    # ======================================================

    result = (
        create_multiscale_targets_v4(
            boxes,
            categories,
            supervision="full",
            num_classes=NUM_CLASSES
        )
    )

    small_target = (
        result[
            "small_target"
        ]
    )

    large_target = (
        result[
            "large_target"
        ]
    )

    print(
        "\nFULL SUPERVISION"
    )

    print(
        "Small target shape:",
        small_target.shape
    )

    print(
        "Large target shape:",
        large_target.shape
    )

    print(
        "Small objects:",
        int(
            small_target[
                0
            ].sum().item()
        )
    )

    print(
        "Large objects:",
        int(
            large_target[
                0
            ].sum().item()
        )
    )

    print(
        "Small collisions:",
        result[
            "small_collisions"
        ]
    )

    print(
        "Large collisions:",
        result[
            "large_collisions"
        ]
    )

    print(
        "Small supervised cells:",
        int(
            result[
                "small_objectness_mask"
            ].sum().item()
        )
    )

    print(
        "Large supervised cells:",
        int(
            result[
                "large_objectness_mask"
            ].sum().item()
        )
    )

    assert (
        small_target.shape
        == (
            20,
            56,
            56
        )
    )

    assert (
        large_target.shape
        == (
            20,
            28,
            28
        )
    )

    assert (
        result[
            "small_objectness_mask"
        ].sum().item()
        == 56 * 56
    )

    assert (
        result[
            "large_objectness_mask"
        ].sum().item()
        == 28 * 28
    )

    print(
        "✅ Full supervision test passed"
    )

    # ======================================================
    # POSITIVE-ONLY TEST
    # ======================================================

    result_positive = (
        create_multiscale_targets_v4(
            boxes,
            categories,
            supervision="positive_only",
            num_classes=NUM_CLASSES
        )
    )

    print(
        "\nPOSITIVE-ONLY SUPERVISION"
    )

    small_positive = int(
        result_positive[
            "small_target"
        ][0].sum().item()
    )

    large_positive = int(
        result_positive[
            "large_target"
        ][0].sum().item()
    )

    small_mask = int(
        result_positive[
            "small_objectness_mask"
        ].sum().item()
    )

    large_mask = int(
        result_positive[
            "large_objectness_mask"
        ].sum().item()
    )

    print(
        "Small positive cells:",
        small_positive
    )

    print(
        "Small supervised cells:",
        small_mask
    )

    print(
        "Large positive cells:",
        large_positive
    )

    print(
        "Large supervised cells:",
        large_mask
    )

    assert (
        small_positive
        == small_mask
    )

    assert (
        large_positive
        == large_mask
    )

    # ======================================================
    # AMBULANCE CLASS TEST
    # ======================================================

    ambulance_channel = (
        5 + 14
    )

    small_ambulance = (
        result_positive[
            "small_target"
        ][
            ambulance_channel
        ].sum().item()
    )

    large_ambulance = (
        result_positive[
            "large_target"
        ][
            ambulance_channel
        ].sum().item()
    )

    total_ambulance = (
        small_ambulance
        + large_ambulance
    )

    print(
        "Ambulance cells:",
        int(
            total_ambulance
        )
    )

    assert (
        total_ambulance >= 1
    )

    print(
        "✅ Positive-only supervision test passed"
    )

    # ======================================================
    # ROUND-TRIP TEST
    # ======================================================

    print(
        "\nROUND-TRIP TEST"
    )

    decoded_small = (
        decode_target_grid_v4(
            result[
                "small_target"
            ],
            grid_size=56
        )
    )

    decoded_large = (
        decode_target_grid_v4(
            result[
                "large_target"
            ],
            grid_size=28
        )
    )

    decoded = (
        decoded_small
        + decoded_large
    )

    minimum_iou = 1.0

    for original_box, category in zip(
        boxes,
        categories
    ):

        original = (
            original_box.tolist()
        )

        class_id = int(
            category.item()
        )

        matching = [
            item
            for item in decoded
            if item[4] == class_id
        ]

        if not matching:

            print(
                f"Class {class_id}: "
                f"NOT FOUND"
            )

            minimum_iou = 0.0

            continue

        best_iou = max(
            box_iou_xywh(
                original,
                candidate[:4]
            )
            for candidate in matching
        )

        minimum_iou = min(
            minimum_iou,
            best_iou
        )

        print(
            f"Class {class_id}: "
            f"IoU = "
            f"{best_iou:.8f}"
        )

    print(
        "Minimum IoU:",
        f"{minimum_iou:.8f}"
    )

    assert (
        minimum_iou > 0.999
    )

    print(
        "✅ Round-trip test passed"
    )

    # ======================================================
    # FINAL
    # ======================================================

    print(
        "\n"
        + "=" * 70
    )

    print(
        "✅ V4 TARGET + SUPERVISION TEST PASSED!"
    )

    print(
        "=" * 70
    )