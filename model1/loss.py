import torch
import torch.nn as nn
import torch.nn.functional as F


# ==================================================
# FOCAL BINARY CROSS ENTROPY
# ==================================================

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

        # Standard BCE for every prediction
        bce_loss = (
            F.binary_cross_entropy_with_logits(
                logits,
                targets,
                reduction="none"
            )
        )


        # Convert logits -> probabilities
        probabilities = torch.sigmoid(
            logits
        )


        # Probability assigned to the
        # correct target class
        p_t = (
            probabilities * targets
            +
            (1.0 - probabilities)
            * (1.0 - targets)
        )


        # Positive / negative balancing
        alpha_t = (
            self.alpha * targets
            +
            (1.0 - self.alpha)
            * (1.0 - targets)
        )


        # Focal weighting
        focal_weight = (
            alpha_t
            *
            (1.0 - p_t).pow(
                self.gamma
            )
        )


        loss = (
            focal_weight
            *
            bce_loss
        )


        return loss.mean()


# ==================================================
# TRAFFIC DETECTION LOSS
# ==================================================

class TrafficDetectionLoss(nn.Module):

    def __init__(
        self,
        lambda_box=5.0,
        lambda_obj=1.0,
        lambda_noobj=0.50,
        lambda_class=1.0,
        focal_alpha=0.25,
        focal_gamma=2.0
    ):

        super().__init__()


        self.lambda_box = lambda_box
        self.lambda_obj = lambda_obj
        self.lambda_noobj = lambda_noobj
        self.lambda_class = lambda_class


        # ==================================================
        # V3 OBJECTNESS LOSS
        # ==================================================
        #
        # V2 used ordinary BCE.
        #
        # V3 uses focal BCE so that the huge number of
        # easy background cells do not dominate training.
        #
        # Hard false positives receive more attention.
        # ==================================================

        self.objectness_loss = (
            FocalBCEWithLogitsLoss(
                alpha=focal_alpha,
                gamma=focal_gamma
            )
        )


        # ==================================================
        # BOX LOSS
        # ==================================================

        self.box_loss = (
            nn.SmoothL1Loss()
        )


        # ==================================================
        # CLASS BALANCING
        # ==================================================

        class_counts = torch.tensor(
            [
                2970,   # Hatchback
                1740,   # Sedan
                1415,   # SUV
                786,    # MUV
                1094,   # Bus
                850,    # Truck
                5671,   # Three-wheeler
                14510,  # Two-wheeler
                1507,   # LCV
                124,    # Mini-bus
                386,    # Tempo-traveller
                374,    # Bicycle
                357,    # Van
                0       # Other
            ],
            dtype=torch.float32
        )


        nonzero_mask = (
            class_counts > 0
        )


        class_weights = torch.zeros_like(
            class_counts
        )


        mean_count = (
            class_counts[
                nonzero_mask
            ].mean()
        )


        # Square-root inverse-frequency weighting
        class_weights[
            nonzero_mask
        ] = torch.sqrt(
            mean_count
            /
            class_counts[
                nonzero_mask
            ]
        )


        # Normalize useful weights
        class_weights[
            nonzero_mask
        ] /= (
            class_weights[
                nonzero_mask
            ].mean()
        )


        # "Other" has no examples
        class_weights[13] = 0.0


        self.register_buffer(
            "class_weights",
            class_weights
        )


        self.class_loss = (
            nn.CrossEntropyLoss(
                weight=self.class_weights
            )
        )


    def forward(
        self,
        predictions,
        targets
    ):

        # predictions:
        # [B, 19, 28, 28]
        #
        # targets:
        # [B, 19, 28, 28]


        # ==================================================
        # OBJECT MASKS
        # ==================================================

        target_objectness = (
            targets[:, 0]
        )


        object_mask = (
            target_objectness > 0.5
        )


        no_object_mask = (
            ~object_mask
        )


        # ==================================================
        # OBJECTNESS PREDICTION
        # ==================================================

        pred_objectness = (
            predictions[:, 0]
        )


        # ==================================================
        # POSITIVE OBJECT CELLS
        # ==================================================

        if object_mask.any():

            object_loss = (
                self.objectness_loss(
                    pred_objectness[
                        object_mask
                    ],
                    target_objectness[
                        object_mask
                    ]
                )
            )

        else:

            object_loss = (
                predictions.sum()
                * 0
            )


        # ==================================================
        # BACKGROUND / NO-OBJECT CELLS
        # ==================================================

        if no_object_mask.any():

            no_object_loss = (
                self.objectness_loss(
                    pred_objectness[
                        no_object_mask
                    ],
                    target_objectness[
                        no_object_mask
                    ]
                )
            )

        else:

            no_object_loss = (
                predictions.sum()
                * 0
            )


        # ==================================================
        # BOUNDING BOX LOSS
        # ==================================================

        pred_boxes = torch.sigmoid(
            predictions[:, 1:5]
        ).permute(
            0,
            2,
            3,
            1
        )


        target_boxes = (
            targets[:, 1:5]
            .permute(
                0,
                2,
                3,
                1
            )
        )


        if object_mask.any():

            box_loss = (
                self.box_loss(
                    pred_boxes[
                        object_mask
                    ],
                    target_boxes[
                        object_mask
                    ]
                )
            )

        else:

            box_loss = (
                predictions.sum()
                * 0
            )


        # ==================================================
        # CLASS LOSS
        # ==================================================

        pred_classes = (
            predictions[:, 5:]
            .permute(
                0,
                2,
                3,
                1
            )
        )


        target_class_ids = (
            torch.argmax(
                targets[:, 5:],
                dim=1
            )
        )


        if object_mask.any():

            class_loss = (
                self.class_loss(
                    pred_classes[
                        object_mask
                    ],
                    target_class_ids[
                        object_mask
                    ]
                )
            )

        else:

            class_loss = (
                predictions.sum()
                * 0
            )


        # ==================================================
        # TOTAL LOSS
        # ==================================================

        total_loss = (

            self.lambda_box
            * box_loss

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
        # RETURN
        # ==================================================

        return (
            total_loss,
            {

                "object":
                    object_loss.item(),

                "no_object":
                    no_object_loss.item(),

                "box":
                    box_loss.item(),

                "class":
                    class_loss.item()

            }
        )