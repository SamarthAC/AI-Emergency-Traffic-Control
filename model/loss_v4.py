import math

import torch
import torch.nn as nn
import torch.nn.functional as F


# ==========================================================
# SETTINGS
# ==========================================================

NUM_CLASSES = 15


# ==========================================================
# BOX CONVERSION
# ==========================================================

def xywh_to_xyxy(boxes):
    """
    boxes:
        [..., 4]

    format:
        center_x, center_y, width, height

    returns:
        x1, y1, x2, y2
    """

    cx = boxes[..., 0]
    cy = boxes[..., 1]

    w = boxes[..., 2]
    h = boxes[..., 3]

    x1 = (
        cx - w / 2.0
    )

    y1 = (
        cy - h / 2.0
    )

    x2 = (
        cx + w / 2.0
    )

    y2 = (
        cy + h / 2.0
    )

    return torch.stack(
        [
            x1,
            y1,
            x2,
            y2
        ],
        dim=-1
    )


# ==========================================================
# COMPLETE IoU
# ==========================================================

def complete_iou(
    pred_boxes,
    target_boxes,
    eps=1e-7
):
    """
    pred_boxes / target_boxes:

        [N, 4]

    format:

        center_x,
        center_y,
        width,
        height

    Returns:
        CIoU for each box pair.
    """

    pred_xyxy = (
        xywh_to_xyxy(
            pred_boxes
        )
    )

    target_xyxy = (
        xywh_to_xyxy(
            target_boxes
        )
    )

    # ======================================================
    # BOX CORNERS
    # ======================================================

    pred_x1 = pred_xyxy[..., 0]
    pred_y1 = pred_xyxy[..., 1]
    pred_x2 = pred_xyxy[..., 2]
    pred_y2 = pred_xyxy[..., 3]

    target_x1 = target_xyxy[..., 0]
    target_y1 = target_xyxy[..., 1]
    target_x2 = target_xyxy[..., 2]
    target_y2 = target_xyxy[..., 3]

    # ======================================================
    # INTERSECTION
    # ======================================================

    inter_x1 = torch.maximum(
        pred_x1,
        target_x1
    )

    inter_y1 = torch.maximum(
        pred_y1,
        target_y1
    )

    inter_x2 = torch.minimum(
        pred_x2,
        target_x2
    )

    inter_y2 = torch.minimum(
        pred_y2,
        target_y2
    )

    inter_w = (
        inter_x2
        - inter_x1
    ).clamp(
        min=0
    )

    inter_h = (
        inter_y2
        - inter_y1
    ).clamp(
        min=0
    )

    intersection = (
        inter_w
        * inter_h
    )

    # ======================================================
    # AREAS
    # ======================================================

    pred_area = (
        (
            pred_x2
            - pred_x1
        ).clamp(
            min=0
        )
        *
        (
            pred_y2
            - pred_y1
        ).clamp(
            min=0
        )
    )

    target_area = (
        (
            target_x2
            - target_x1
        ).clamp(
            min=0
        )
        *
        (
            target_y2
            - target_y1
        ).clamp(
            min=0
        )
    )

    union = (
        pred_area
        + target_area
        - intersection
        + eps
    )

    iou = (
        intersection
        / union
    )

    # ======================================================
    # CENTER DISTANCE
    # ======================================================

    pred_cx = pred_boxes[..., 0]
    pred_cy = pred_boxes[..., 1]

    target_cx = target_boxes[..., 0]
    target_cy = target_boxes[..., 1]

    center_distance_squared = (
        (
            pred_cx
            - target_cx
        ) ** 2
        +
        (
            pred_cy
            - target_cy
        ) ** 2
    )

    # ======================================================
    # SMALLEST ENCLOSING BOX
    # ======================================================

    enclosing_x1 = torch.minimum(
        pred_x1,
        target_x1
    )

    enclosing_y1 = torch.minimum(
        pred_y1,
        target_y1
    )

    enclosing_x2 = torch.maximum(
        pred_x2,
        target_x2
    )

    enclosing_y2 = torch.maximum(
        pred_y2,
        target_y2
    )

    enclosing_diagonal_squared = (
        (
            enclosing_x2
            - enclosing_x1
        ) ** 2
        +
        (
            enclosing_y2
            - enclosing_y1
        ) ** 2
        +
        eps
    )

    # ======================================================
    # ASPECT RATIO TERM
    # ======================================================

    pred_w = pred_boxes[
        ...,
        2
    ].clamp(
        min=eps
    )

    pred_h = pred_boxes[
        ...,
        3
    ].clamp(
        min=eps
    )

    target_w = target_boxes[
        ...,
        2
    ].clamp(
        min=eps
    )

    target_h = target_boxes[
        ...,
        3
    ].clamp(
        min=eps
    )

    v = (
        4.0
        / (
            math.pi ** 2
        )
        *
        (
            torch.atan(
                target_w
                / target_h
            )
            -
            torch.atan(
                pred_w
                / pred_h
            )
        ) ** 2
    )

    with torch.no_grad():

        alpha = (
            v
            /
            (
                1.0
                - iou
                + v
                + eps
            )
        )

    # ======================================================
    # CIoU
    # ======================================================

    ciou = (
        iou
        -
        (
            center_distance_squared
            /
            enclosing_diagonal_squared
        )
        -
        alpha * v
    )

    return ciou


# ==========================================================
# CIoU LOSS
# ==========================================================

def ciou_loss(
    pred_boxes,
    target_boxes
):

    ciou = complete_iou(
        pred_boxes,
        target_boxes
    )

    return (
        1.0
        - ciou
    ).mean()


# ==========================================================
# FOCAL OBJECTNESS LOSS
# ==========================================================

class FocalBCEWithLogitsLoss(nn.Module):

    def __init__(
        self,
        alpha=0.25,
        gamma=2.0
    ):

        super().__init__()

        self.alpha = alpha
        self.gamma = gamma

    def forward(
        self,
        logits,
        targets
    ):

        bce = (
            F.binary_cross_entropy_with_logits(
                logits,
                targets,
                reduction="none"
            )
        )

        probabilities = (
            torch.sigmoid(
                logits
            )
        )

        p_t = (
            probabilities
            * targets
            +
            (
                1.0
                - probabilities
            )
            *
            (
                1.0
                - targets
            )
        )

        alpha_t = (
            self.alpha
            * targets
            +
            (
                1.0
                - self.alpha
            )
            *
            (
                1.0
                - targets
            )
        )

        focal_weight = (
            alpha_t
            *
            (
                1.0
                - p_t
            ) ** self.gamma
        )

        return (
            focal_weight
            * bce
        )


# ==========================================================
# SINGLE-SCALE V4 DETECTION LOSS
# ==========================================================

class TrafficDetectionLossV4(nn.Module):

    def __init__(
        self,
        num_classes=NUM_CLASSES,
        grid_size=28,
        lambda_box=5.0,
        lambda_obj=1.0,
        lambda_noobj=0.50,
        lambda_class=1.0,
        class_weights=None
    ):

        super().__init__()

        self.num_classes = (
            num_classes
        )

        self.grid_size = (
            grid_size
        )

        self.lambda_box = (
            lambda_box
        )

        self.lambda_obj = (
            lambda_obj
        )

        self.lambda_noobj = (
            lambda_noobj
        )

        self.lambda_class = (
            lambda_class
        )

        self.objectness_loss = (
            FocalBCEWithLogitsLoss(
                alpha=0.25,
                gamma=2.0
            )
        )

        # ==================================================
        # CLASS WEIGHTS
        # ==================================================

        if class_weights is not None:

            if (
                len(class_weights)
                != num_classes
            ):

                raise ValueError(
                    "class_weights length "
                    f"({len(class_weights)}) "
                    "must equal num_classes "
                    f"({num_classes})."
                )

            self.register_buffer(
                "class_weights",
                torch.tensor(
                    class_weights,
                    dtype=torch.float32
                )
            )

        else:

            self.class_weights = None

    # ======================================================
    # DECODE PREDICTED BOXES
    # ======================================================

    def decode_boxes(
        self,
        raw_boxes
    ):
        """
        raw_boxes:

            [B, 4, H, W]

        Returns:

            [B, H, W, 4]

        format:

            center_x,
            center_y,
            width,
            height
        """

        height = (
            raw_boxes.shape[2]
        )

        width = (
            raw_boxes.shape[3]
        )

        device = (
            raw_boxes.device
        )

        dtype = (
            raw_boxes.dtype
        )

        offset_x = (
            torch.sigmoid(
                raw_boxes[:, 0]
            )
        )

        offset_y = (
            torch.sigmoid(
                raw_boxes[:, 1]
            )
        )

        box_w = (
            torch.sigmoid(
                raw_boxes[:, 2]
            )
        )

        box_h = (
            torch.sigmoid(
                raw_boxes[:, 3]
            )
        )

        grid_y, grid_x = (
            torch.meshgrid(
                torch.arange(
                    height,
                    device=device,
                    dtype=dtype
                ),
                torch.arange(
                    width,
                    device=device,
                    dtype=dtype
                ),
                indexing="ij"
            )
        )

        center_x = (
            grid_x.unsqueeze(0)
            + offset_x
        ) / width

        center_y = (
            grid_y.unsqueeze(0)
            + offset_y
        ) / height

        decoded = torch.stack(
            [
                center_x,
                center_y,
                box_w,
                box_h
            ],
            dim=-1
        )

        return decoded

    # ======================================================
    # DECODE TARGET BOXES
    # ======================================================

    def decode_target_boxes(
        self,
        target
    ):
        """
        target:

            [B, 5 + num_classes, H, W]

        Returns:

            [B, H, W, 4]

        format:

            center_x,
            center_y,
            width,
            height
        """

        height = (
            target.shape[2]
        )

        width = (
            target.shape[3]
        )

        device = (
            target.device
        )

        dtype = (
            target.dtype
        )

        offset_x = (
            target[:, 1]
        )

        offset_y = (
            target[:, 2]
        )

        box_w = (
            target[:, 3]
        )

        box_h = (
            target[:, 4]
        )

        grid_y, grid_x = (
            torch.meshgrid(
                torch.arange(
                    height,
                    device=device,
                    dtype=dtype
                ),
                torch.arange(
                    width,
                    device=device,
                    dtype=dtype
                ),
                indexing="ij"
            )
        )

        center_x = (
            grid_x.unsqueeze(0)
            + offset_x
        ) / width

        center_y = (
            grid_y.unsqueeze(0)
            + offset_y
        ) / height

        decoded = torch.stack(
            [
                center_x,
                center_y,
                box_w,
                box_h
            ],
            dim=-1
        )

        return decoded

    # ======================================================
    # FORWARD
    # ======================================================

    def forward(
        self,
        predictions,
        targets,
        objectness_supervision_mask=None
    ):
        """
        predictions:

            [B, 5 + num_classes, H, W]

        targets:

            [B, 5 + num_classes, H, W]

        objectness_supervision_mask:

            [B, H, W]

            1 = objectness supervision allowed
            0 = ignore objectness at this cell

        For BMD/full-supervision samples:
            mask is all 1.

        For ambulance/positive-only samples:
            mask is 1 only at known ambulance cells.
        """

        # ==================================================
        # SHAPE VALIDATION
        # ==================================================

        expected_channels = (
            5
            + self.num_classes
        )

        if (
            predictions.shape[1]
            != expected_channels
        ):

            raise ValueError(
                "Prediction channel mismatch. "
                f"Expected {expected_channels}, "
                f"got {predictions.shape[1]}."
            )

        if (
            targets.shape[1]
            != expected_channels
        ):

            raise ValueError(
                "Target channel mismatch. "
                f"Expected {expected_channels}, "
                f"got {targets.shape[1]}."
            )

        # ==================================================
        # POSITIVE OBJECT MASK
        # ==================================================

        object_mask = (
            targets[:, 0]
            > 0.5
        )

        # ==================================================
        # SUPERVISION MASK
        # ==================================================

        if (
            objectness_supervision_mask
            is None
        ):

            # Backward-compatible default:
            # every cell supervised.
            supervision_mask = (
                torch.ones_like(
                    targets[:, 0],
                    dtype=torch.bool
                )
            )

        else:

            if (
                objectness_supervision_mask.shape
                != targets[:, 0].shape
            ):

                raise ValueError(
                    "Objectness supervision mask "
                    "shape mismatch. "
                    f"Expected "
                    f"{targets[:, 0].shape}, "
                    f"got "
                    f"{objectness_supervision_mask.shape}."
                )

            supervision_mask = (
                objectness_supervision_mask
                > 0.5
            )

        # Positive cells MUST always remain
        # supervised.
        #
        # This is a safety measure in case a malformed
        # external mask accidentally marks a positive
        # target as ignored.
        supervision_mask = (
            supervision_mask
            | object_mask
        )

        # ==================================================
        # NEGATIVE / NO-OBJECT MASK
        # ==================================================
        #
        # This is the critical V4 change:
        #
        # old:
        #     no_object_mask = ~object_mask
        #
        # new:
        #     empty AND supervised
        #
        # Therefore ignored cells from ambulance images
        # do not contribute background loss.
        # ==================================================

        no_object_mask = (
            (~object_mask)
            & supervision_mask
        )

        # ==================================================
        # OBJECTNESS
        # ==================================================

        objectness_logits = (
            predictions[:, 0]
        )

        objectness_targets = (
            targets[:, 0]
        )

        objectness_map = (
            self.objectness_loss(
                objectness_logits,
                objectness_targets
            )
        )

        # --------------------------------------------------
        # POSITIVE OBJECTNESS LOSS
        # --------------------------------------------------

        if object_mask.any():

            object_loss = (
                objectness_map[
                    object_mask
                ].mean()
            )

        else:

            object_loss = (
                predictions.sum()
                * 0.0
            )

        # --------------------------------------------------
        # NEGATIVE OBJECTNESS LOSS
        # --------------------------------------------------

        if no_object_mask.any():

            no_object_loss = (
                objectness_map[
                    no_object_mask
                ].mean()
            )

        else:

            # Important for positive-only ambulance
            # images where there may be zero supervised
            # background cells.
            no_object_loss = (
                predictions.sum()
                * 0.0
            )

        # ==================================================
        # BBOX CIoU
        # ==================================================

        if object_mask.any():

            predicted_boxes = (
                self.decode_boxes(
                    predictions[:, 1:5]
                )
            )

            target_boxes = (
                self.decode_target_boxes(
                    targets
                )
            )

            predicted_positive_boxes = (
                predicted_boxes[
                    object_mask
                ]
            )

            target_positive_boxes = (
                target_boxes[
                    object_mask
                ]
            )

            bbox_loss = (
                ciou_loss(
                    predicted_positive_boxes,
                    target_positive_boxes
                )
            )

        else:

            bbox_loss = (
                predictions.sum()
                * 0.0
            )

        # ==================================================
        # CLASSIFICATION
        # ==================================================

        if object_mask.any():

            class_logits = (
                predictions[
                    :,
                    5:
                ]
                .permute(
                    0,
                    2,
                    3,
                    1
                )
            )

            target_classes = (
                targets[
                    :,
                    5:
                ]
                .argmax(
                    dim=1
                )
            )

            positive_class_logits = (
                class_logits[
                    object_mask
                ]
            )

            positive_target_classes = (
                target_classes[
                    object_mask
                ]
            )

            class_loss = (
                F.cross_entropy(
                    positive_class_logits,
                    positive_target_classes,
                    weight=self.class_weights
                )
            )

        else:

            class_loss = (
                predictions.sum()
                * 0.0
            )

        # ==================================================
        # TOTAL
        # ==================================================

        total_loss = (
            self.lambda_box
            * bbox_loss

            +

            self.lambda_obj
            * object_loss

            +

            self.lambda_noobj
            * no_object_loss

            +

            self.lambda_class
            * class_loss
        )

        # ==================================================
        # DIAGNOSTIC COUNTS
        # ==================================================

        supervised_positive_cells = (
            object_mask.sum()
        )

        supervised_negative_cells = (
            no_object_mask.sum()
        )

        ignored_cells = (
            (
                ~supervision_mask
            )
            .sum()
        )

        # ==================================================
        # RETURN
        # ==================================================

        return {

            "total":
                total_loss,

            "box":
                bbox_loss,

            "object":
                object_loss,

            "no_object":
                no_object_loss,

            "class":
                class_loss,

            "positive_cells":
                supervised_positive_cells,

            "negative_cells":
                supervised_negative_cells,

            "ignored_cells":
                ignored_cells
        }


# ==========================================================
# MULTI-SCALE LOSS
# ==========================================================

class MultiScaleTrafficLossV4(nn.Module):
    """
    Combines:

        56x56 small-object head
        28x28 medium/large-object head
    """

    def __init__(
        self,
        num_classes=NUM_CLASSES,
        lambda_box=5.0,
        lambda_obj=1.0,
        lambda_noobj=0.50,
        lambda_class=1.0,
        class_weights=None,
        small_scale_weight=1.0,
        large_scale_weight=1.0
    ):

        super().__init__()

        self.small_scale_weight = (
            small_scale_weight
        )

        self.large_scale_weight = (
            large_scale_weight
        )

        self.small_loss = (
            TrafficDetectionLossV4(
                num_classes=num_classes,
                grid_size=56,
                lambda_box=lambda_box,
                lambda_obj=lambda_obj,
                lambda_noobj=lambda_noobj,
                lambda_class=lambda_class,
                class_weights=class_weights
            )
        )

        self.large_loss = (
            TrafficDetectionLossV4(
                num_classes=num_classes,
                grid_size=28,
                lambda_box=lambda_box,
                lambda_obj=lambda_obj,
                lambda_noobj=lambda_noobj,
                lambda_class=lambda_class,
                class_weights=class_weights
            )
        )

    # ======================================================
    # FORWARD
    # ======================================================

    def forward(
        self,
        predictions,
        targets,
        objectness_masks=None
    ):
        """
        predictions:

            {
                "small": [B,20,56,56],
                "large": [B,20,28,28]
            }

        targets:

            {
                "small": [B,20,56,56],
                "large": [B,20,28,28]
            }

        objectness_masks:

            {
                "small": [B,56,56],
                "large": [B,28,28]
            }

        If objectness_masks is None,
        all cells receive normal supervision.
        """

        if objectness_masks is None:

            small_mask = None
            large_mask = None

        else:

            small_mask = (
                objectness_masks[
                    "small"
                ]
            )

            large_mask = (
                objectness_masks[
                    "large"
                ]
            )

        # ==================================================
        # SMALL HEAD
        # ==================================================

        small_losses = (
            self.small_loss(
                predictions[
                    "small"
                ],
                targets[
                    "small"
                ],
                objectness_supervision_mask=(
                    small_mask
                )
            )
        )

        # ==================================================
        # LARGE HEAD
        # ==================================================

        large_losses = (
            self.large_loss(
                predictions[
                    "large"
                ],
                targets[
                    "large"
                ],
                objectness_supervision_mask=(
                    large_mask
                )
            )
        )

        # ==================================================
        # TOTAL
        # ==================================================

        total = (
            self.small_scale_weight
            * small_losses[
                "total"
            ]

            +

            self.large_scale_weight
            * large_losses[
                "total"
            ]
        )

        return {

            "total":
                total,

            # SMALL
            "small_total":
                small_losses[
                    "total"
                ],

            "small_box":
                small_losses[
                    "box"
                ],

            "small_object":
                small_losses[
                    "object"
                ],

            "small_no_object":
                small_losses[
                    "no_object"
                ],

            "small_class":
                small_losses[
                    "class"
                ],

            "small_positive_cells":
                small_losses[
                    "positive_cells"
                ],

            "small_negative_cells":
                small_losses[
                    "negative_cells"
                ],

            "small_ignored_cells":
                small_losses[
                    "ignored_cells"
                ],

            # LARGE
            "large_total":
                large_losses[
                    "total"
                ],

            "large_box":
                large_losses[
                    "box"
                ],

            "large_object":
                large_losses[
                    "object"
                ],

            "large_no_object":
                large_losses[
                    "no_object"
                ],

            "large_class":
                large_losses[
                    "class"
                ],

            "large_positive_cells":
                large_losses[
                    "positive_cells"
                ],

            "large_negative_cells":
                large_losses[
                    "negative_cells"
                ],

            "large_ignored_cells":
                large_losses[
                    "ignored_cells"
                ]
        }


# ==========================================================
# TESTS
# ==========================================================

if __name__ == "__main__":

    print(
        "=" * 70
    )

    print(
        "V4 LOSS TEST"
    )

    print(
        "=" * 70
    )

    # ======================================================
    # TEST 1 — CIoU
    # ======================================================

    target_box = torch.tensor(
        [
            [
                0.50,
                0.50,
                0.20,
                0.20
            ]
        ],
        dtype=torch.float32
    )

    identical = (
        target_box
        .clone()
        .requires_grad_()
    )

    slightly_shifted = (
        torch.tensor(
            [
                [
                    0.53,
                    0.52,
                    0.20,
                    0.20
                ]
            ],
            dtype=torch.float32,
            requires_grad=True
        )
    )

    bad_box = (
        torch.tensor(
            [
                [
                    0.80,
                    0.80,
                    0.10,
                    0.10
                ]
            ],
            dtype=torch.float32,
            requires_grad=True
        )
    )

    loss_identical = (
        ciou_loss(
            identical,
            target_box
        )
    )

    loss_shifted = (
        ciou_loss(
            slightly_shifted,
            target_box
        )
    )

    loss_bad = (
        ciou_loss(
            bad_box,
            target_box
        )
    )

    print(
        "\nCIoU TEST"
    )

    print(
        "Identical:",
        f"{loss_identical.item():.8f}"
    )

    print(
        "Shifted:",
        f"{loss_shifted.item():.8f}"
    )

    print(
        "Bad:",
        f"{loss_bad.item():.8f}"
    )

    identical_ok = (
        loss_identical.item()
        < 1e-5
    )

    ordering_ok = (
        loss_identical.item()
        <
        loss_shifted.item()
        <
        loss_bad.item()
    )

    loss_shifted.backward()

    gradient_ok = (
        slightly_shifted.grad
        is not None
        and
        torch.isfinite(
            slightly_shifted.grad
        ).all()
    )

    assert identical_ok
    assert ordering_ok
    assert gradient_ok

    print(
        "✅ CIoU TEST PASSED"
    )

    # ======================================================
    # TEST 2 — FULL SUPERVISION
    # ======================================================

    print(
        "\nFULL SUPERVISION LOSS TEST"
    )

    loss_function = (
        TrafficDetectionLossV4(
            num_classes=15,
            grid_size=28
        )
    )

    predictions = (
        torch.randn(
            1,
            20,
            28,
            28,
            requires_grad=True
        )
    )

    targets = torch.zeros(
        1,
        20,
        28,
        28
    )

    # One object
    targets[
        0,
        0,
        10,
        12
    ] = 1.0

    targets[
        0,
        1,
        10,
        12
    ] = 0.5

    targets[
        0,
        2,
        10,
        12
    ] = 0.5

    targets[
        0,
        3,
        10,
        12
    ] = 0.20

    targets[
        0,
        4,
        10,
        12
    ] = 0.15

    # Ambulance class 14
    targets[
        0,
        5 + 14,
        10,
        12
    ] = 1.0

    full_mask = torch.ones(
        1,
        28,
        28
    )

    full_losses = (
        loss_function(
            predictions,
            targets,
            full_mask
        )
    )

    print(
        "Positive cells:",
        int(
            full_losses[
                "positive_cells"
            ].item()
        )
    )

    print(
        "Negative cells:",
        int(
            full_losses[
                "negative_cells"
            ].item()
        )
    )

    print(
        "Ignored cells:",
        int(
            full_losses[
                "ignored_cells"
            ].item()
        )
    )

    assert (
        full_losses[
            "positive_cells"
        ].item()
        == 1
    )

    assert (
        full_losses[
            "negative_cells"
        ].item()
        == (
            28 * 28
            - 1
        )
    )

    assert (
        full_losses[
            "ignored_cells"
        ].item()
        == 0
    )

    print(
        "✅ FULL SUPERVISION LOSS PASSED"
    )

    # ======================================================
    # TEST 3 — POSITIVE-ONLY
    # ======================================================

    print(
        "\nPOSITIVE-ONLY LOSS TEST"
    )

    positive_only_mask = (
        torch.zeros(
            1,
            28,
            28
        )
    )

    positive_only_mask[
        0,
        10,
        12
    ] = 1.0

    positive_losses = (
        loss_function(
            predictions,
            targets,
            positive_only_mask
        )
    )

    print(
        "Positive cells:",
        int(
            positive_losses[
                "positive_cells"
            ].item()
        )
    )

    print(
        "Negative cells:",
        int(
            positive_losses[
                "negative_cells"
            ].item()
        )
    )

    print(
        "Ignored cells:",
        int(
            positive_losses[
                "ignored_cells"
            ].item()
        )
    )

    print(
        "No-object loss:",
        float(
            positive_losses[
                "no_object"
            ].detach().item()
        )
    )

    assert (
        positive_losses[
            "positive_cells"
        ].item()
        == 1
    )

    assert (
        positive_losses[
            "negative_cells"
        ].item()
        == 0
    )

    assert (
        positive_losses[
            "ignored_cells"
        ].item()
        == (
            28 * 28
            - 1
        )
    )

    assert (
        abs(
            positive_losses[
                "no_object"
            ].detach().item()
        )
        < 1e-8
    )

    print(
        "✅ POSITIVE-ONLY LOSS PASSED"
    )

    # ======================================================
    # BACKWARD
    # ======================================================

    total = (
        full_losses[
            "total"
        ]
        +
        positive_losses[
            "total"
        ]
    )

    total.backward()

    gradients_ok = (
        predictions.grad
        is not None
        and
        torch.isfinite(
            predictions.grad
        ).all()
    )

    assert gradients_ok

    print(
        "✅ LOSS BACKWARD PASSED"
    )

    # ======================================================
    # FINAL
    # ======================================================

    print(
        "\n"
        + "=" * 70
    )

    print(
        "✅ V4 MASKED LOSS TEST PASSED!"
    )

    print(
        "=" * 70
    )