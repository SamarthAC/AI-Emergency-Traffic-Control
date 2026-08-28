import torch
import torch.nn as nn


class DetectionLoss(nn.Module):

    def __init__(
        self,
        lambda_box=5.0,
        lambda_obj=1.0,
        lambda_noobj=0.25,
        lambda_class=1.0
    ):
        super().__init__()

        self.lambda_box = lambda_box
        self.lambda_obj = lambda_obj
        self.lambda_noobj = lambda_noobj
        self.lambda_class = lambda_class

        self.bce = nn.BCEWithLogitsLoss()
        self.box_loss = nn.SmoothL1Loss()
        self.cross_entropy = nn.CrossEntropyLoss()

    def forward(self, predictions, targets):

        # -----------------------------------
        # Masks
        # -----------------------------------
        object_mask = targets[:, 0] == 1
        no_object_mask = targets[:, 0] == 0

        # -----------------------------------
        # OBJECTNESS LOSS
        # -----------------------------------
        obj_loss = self.bce(
            predictions[:, 0][object_mask],
            targets[:, 0][object_mask]
        )

        noobj_loss = self.bce(
            predictions[:, 0][no_object_mask],
            targets[:, 0][no_object_mask]
        )

        # -----------------------------------
        # BOUNDING BOX LOSS
        # Only calculate where vehicles exist
        # -----------------------------------
        pred_boxes = torch.sigmoid(predictions[:, 1:5]).permute(0, 2, 3, 1)
        target_boxes = targets[:, 1:5].permute(0, 2, 3, 1)

        box_loss = self.box_loss(
            pred_boxes[object_mask],
            target_boxes[object_mask]
        )

        # -----------------------------------
        # CLASSIFICATION LOSS
        # -----------------------------------
        pred_classes = predictions[:, 5:].permute(0, 2, 3, 1)
        target_classes = targets[:, 5:].permute(0, 2, 3, 1)

        pred_classes = pred_classes[object_mask]
        target_classes = target_classes[object_mask]

        class_ids = torch.argmax(
            target_classes,
            dim=1
        )

        class_loss = self.cross_entropy(
            pred_classes,
            class_ids
        )

        # -----------------------------------
        # TOTAL LOSS
        # -----------------------------------
        total_loss = (
            self.lambda_obj * obj_loss
            + self.lambda_noobj * noobj_loss
            + self.lambda_box * box_loss
            + self.lambda_class * class_loss
        )

        return {
            "total": total_loss,
            "object": obj_loss,
            "no_object": noobj_loss,
            "box": box_loss,
            "class": class_loss
        }