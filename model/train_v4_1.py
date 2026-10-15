import copy
import random
import time
from pathlib import Path

import torch
from torch.utils.data import DataLoader, ConcatDataset, Dataset

from model_v4 import TrafficDetectorV4
from traffic_dataset_v4 import TrafficDatasetV4
from target_generator_v4 import create_multiscale_targets_v4
from loss_v4 import MultiScaleTrafficLossV4


# ==========================================================
# V4.1 TARGETED FINE-TUNING CONFIG
# ==========================================================

SEED = 42
NUM_CLASSES = 15
IMAGE_SIZE = 448

BATCH_SIZE = 8
NUM_WORKERS = 4

# Fine-tuning, not training from scratch.
EPOCHS = 12
LEARNING_RATE = 1e-4
WEIGHT_DECAY = 1e-4
GRAD_CLIP = 5.0
EARLY_STOPPING_PATIENCE = 4

# V4 used lambda_box=5. V4.1 increases localization emphasis
# while retaining objectness + classification supervision.
LAMBDA_BOX = 8.0
LAMBDA_OBJ = 1.0
LAMBDA_NOOBJ = 0.50
LAMBDA_CLASS = 1.0

CLASS_WEIGHTS = [
    0.5167, 0.6865, 0.7775, 1.0168, 0.8197,
    0.9757, 0.3778, 0.2342, 0.7230, 2.5634,
    1.4951, 1.4157, 1.5117, 0.0000, 0.8861
]

MODEL_DIR = Path(__file__).resolve().parent
PROJECT_DIR = MODEL_DIR.parent

START_MODEL = MODEL_DIR / "traffic_detector_v4_best.pth"

BEST_MODEL = MODEL_DIR / "traffic_detector_v4_1_best.pth"
LAST_MODEL = MODEL_DIR / "traffic_detector_v4_1_last.pth"
CHECKPOINT = MODEL_DIR / "traffic_detector_v4_1_checkpoint.pth"

BMD_TRAIN_IMAGES = PROJECT_DIR / "dataset_v4" / "train" / "images"
BMD_TRAIN_LABELS = PROJECT_DIR / "dataset_v4" / "train" / "labels"
BMD_VAL_IMAGES = PROJECT_DIR / "dataset_v4" / "val" / "images"
BMD_VAL_LABELS = PROJECT_DIR / "dataset_v4" / "val" / "labels"

AMB_TRAIN_IMAGES = PROJECT_DIR / "ambulance_v4" / "train" / "images"
AMB_TRAIN_LABELS = PROJECT_DIR / "ambulance_v4" / "train" / "labels"
AMB_VAL_IMAGES = PROJECT_DIR / "ambulance_v4" / "valid" / "images"
AMB_VAL_LABELS = PROJECT_DIR / "ambulance_v4" / "valid" / "labels"


# ==========================================================
# REPRODUCIBILITY / SPEED
# ==========================================================

random.seed(SEED)
torch.manual_seed(SEED)
if torch.cuda.is_available():
    torch.cuda.manual_seed_all(SEED)

torch.backends.cudnn.benchmark = True
if torch.cuda.is_available():
    torch.backends.cuda.matmul.allow_tf32 = True
    torch.backends.cudnn.allow_tf32 = True

try:
    torch.set_float32_matmul_precision("high")
except Exception:
    pass


# ==========================================================
# DATASET SOURCE WRAPPER
# ==========================================================

class SourceDataset(Dataset):
    def __init__(self, dataset, source):
        self.dataset = dataset
        self.source = source

    def __len__(self):
        return len(self.dataset)

    def __getitem__(self, index):
        image, boxes, categories, supervision = self.dataset[index]
        return image, boxes, categories, supervision, self.source


def collate_fn(batch):
    images = torch.stack([x[0] for x in batch], dim=0)
    boxes = [x[1] for x in batch]
    categories = [x[2] for x in batch]
    supervision = [x[3] for x in batch]
    sources = [x[4] for x in batch]
    return images, boxes, categories, supervision, sources


def make_loader(dataset, shuffle, device):
    args = {
        "batch_size": BATCH_SIZE,
        "shuffle": shuffle,
        "num_workers": NUM_WORKERS,
        "pin_memory": device.type == "cuda",
        "collate_fn": collate_fn,
    }

    if NUM_WORKERS > 0:
        args["persistent_workers"] = True
        args["prefetch_factor"] = 2

    return DataLoader(dataset, **args)


# ==========================================================
# TARGET BUILDING
# ==========================================================

def build_batch_targets(boxes_batch, categories_batch, supervision_batch, device):
    small_targets = []
    large_targets = []
    small_masks = []
    large_masks = []
    collisions = 0

    for boxes, categories, supervision in zip(
        boxes_batch, categories_batch, supervision_batch
    ):
        result = create_multiscale_targets_v4(
            boxes,
            categories,
            supervision=supervision,
            num_classes=NUM_CLASSES,
            image_size=IMAGE_SIZE,
        )

        small_targets.append(result["small_target"])
        large_targets.append(result["large_target"])
        small_masks.append(result["small_objectness_mask"])
        large_masks.append(result["large_objectness_mask"])

        collisions += (
            int(result["small_collisions"])
            + int(result["large_collisions"])
        )

    targets = {
        "small": torch.stack(small_targets).to(device, non_blocking=True),
        "large": torch.stack(large_targets).to(device, non_blocking=True),
    }

    masks = {
        "small": torch.stack(small_masks).to(device, non_blocking=True),
        "large": torch.stack(large_masks).to(device, non_blocking=True),
    }

    return targets, masks, collisions


# ==========================================================
# CHECKPOINT LOADING
# ==========================================================

def extract_state_dict(obj):
    if isinstance(obj, dict) and "model_state_dict" in obj:
        return obj["model_state_dict"]
    if isinstance(obj, dict) and "model" in obj and isinstance(obj["model"], dict):
        return obj["model"]
    return obj


def load_v4_baseline(model, device):
    if not START_MODEL.exists():
        raise FileNotFoundError(
            f"V4 baseline checkpoint not found:\n{START_MODEL}"
        )

    loaded = torch.load(
        START_MODEL,
        map_location=device,
        weights_only=True,
    )
    model.load_state_dict(extract_state_dict(loaded))

    print("Loaded V4 baseline:")
    print(START_MODEL)


# ==========================================================
# TRAIN / VALIDATE
# ==========================================================

def run_epoch(
    model,
    loader,
    loss_fn,
    device,
    optimizer=None,
    scaler=None,
):
    training = optimizer is not None

    if training:
        model.train()
    else:
        model.eval()

    totals = {
        "loss": 0.0,
        "small": 0.0,
        "large": 0.0,
        "samples": 0,
        "bmd": 0,
        "ambulance": 0,
        "collisions": 0,
    }

    context = torch.enable_grad() if training else torch.inference_mode()

    with context:
        for images, boxes, categories, supervision, sources in loader:
            images = images.to(device, non_blocking=True)

            targets, masks, collisions = build_batch_targets(
                boxes,
                categories,
                supervision,
                device,
            )

            if training:
                optimizer.zero_grad(set_to_none=True)

            with torch.amp.autocast(
                device_type=device.type,
                dtype=torch.float16,
                enabled=device.type == "cuda",
            ):
                predictions = model(images)

                losses = loss_fn(
                    predictions,
                    targets,
                    objectness_masks=masks,
                )

                loss = losses["total"]

            if training:
                scaler.scale(loss).backward()
                scaler.unscale_(optimizer)

                torch.nn.utils.clip_grad_norm_(
                    model.parameters(),
                    GRAD_CLIP,
                )

                scaler.step(optimizer)
                scaler.update()

            batch_size = images.shape[0]

            totals["loss"] += float(loss.detach()) * batch_size
            totals["small"] += float(losses["small_total"].detach()) * batch_size
            totals["large"] += float(losses["large_total"].detach()) * batch_size
            totals["samples"] += batch_size
            totals["bmd"] += sum(s == "bmd" for s in sources)
            totals["ambulance"] += sum(s == "ambulance" for s in sources)
            totals["collisions"] += collisions

    n = max(1, totals["samples"])

    return {
        "loss": totals["loss"] / n,
        "small": totals["small"] / n,
        "large": totals["large"] / n,
        "samples": totals["samples"],
        "bmd": totals["bmd"],
        "ambulance": totals["ambulance"],
        "collisions": totals["collisions"],
    }


# ==========================================================
# MAIN
# ==========================================================

def main():
    required = [
        START_MODEL,
        BMD_TRAIN_IMAGES, BMD_TRAIN_LABELS,
        BMD_VAL_IMAGES, BMD_VAL_LABELS,
        AMB_TRAIN_IMAGES, AMB_TRAIN_LABELS,
        AMB_VAL_IMAGES, AMB_VAL_LABELS,
    ]

    for path in required:
        if not path.exists():
            raise FileNotFoundError(f"Missing required path:\n{path}")

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    print("=" * 90)
    print("V4.1 TARGETED FINE-TUNING")
    print("=" * 90)
    print("Device       :", device)
    print("Start model  :", START_MODEL)
    print("Best output  :", BEST_MODEL)
    print("Epochs       :", EPOCHS)
    print("Batch size   :", BATCH_SIZE)
    print("LR           :", LEARNING_RATE)
    print("BBox lambda  :", LAMBDA_BOX)
    print("=" * 90)

    # ------------------------------------------------------
    # DATASETS
    # ------------------------------------------------------

    bmd_train = SourceDataset(
        TrafficDatasetV4(
            BMD_TRAIN_IMAGES,
            BMD_TRAIN_LABELS,
            image_size=IMAGE_SIZE,
            augment=True,
        ),
        "bmd",
    )

    ambulance_train = SourceDataset(
        TrafficDatasetV4(
            AMB_TRAIN_IMAGES,
            AMB_TRAIN_LABELS,
            image_size=IMAGE_SIZE,
            augment=True,
        ),
        "ambulance",
    )

    bmd_val = SourceDataset(
        TrafficDatasetV4(
            BMD_VAL_IMAGES,
            BMD_VAL_LABELS,
            image_size=IMAGE_SIZE,
            augment=False,
        ),
        "bmd",
    )

    ambulance_val = SourceDataset(
        TrafficDatasetV4(
            AMB_VAL_IMAGES,
            AMB_VAL_LABELS,
            image_size=IMAGE_SIZE,
            augment=False,
        ),
        "ambulance",
    )

    train_dataset = ConcatDataset([bmd_train, ambulance_train])
    val_dataset = ConcatDataset([bmd_val, ambulance_val])

    train_loader = make_loader(
        train_dataset,
        shuffle=True,
        device=device,
    )

    val_loader = make_loader(
        val_dataset,
        shuffle=False,
        device=device,
    )

    print("Train samples :", len(train_dataset))
    print("  BMD         :", len(bmd_train))
    print("  Ambulance   :", len(ambulance_train))
    print("Val samples   :", len(val_dataset))
    print("  BMD         :", len(bmd_val))
    print("  Ambulance   :", len(ambulance_val))

    # ------------------------------------------------------
    # MODEL / LOSS
    # ------------------------------------------------------

    model = TrafficDetectorV4(
        num_classes=NUM_CLASSES
    ).to(device)

    load_v4_baseline(model, device)

    loss_fn = MultiScaleTrafficLossV4(
        num_classes=NUM_CLASSES,
        lambda_box=LAMBDA_BOX,
        lambda_obj=LAMBDA_OBJ,
        lambda_noobj=LAMBDA_NOOBJ,
        lambda_class=LAMBDA_CLASS,
        class_weights=CLASS_WEIGHTS,
        small_scale_weight=1.0,
        large_scale_weight=1.0,
    ).to(device)

    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=LEARNING_RATE,
        weight_decay=WEIGHT_DECAY,
    )

    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
        optimizer,
        mode="min",
        factor=0.5,
        patience=1,
        min_lr=1e-6,
    )

    scaler = torch.amp.GradScaler(
        "cuda",
        enabled=device.type == "cuda",
    )

    # ------------------------------------------------------
    # FINE-TUNE
    # ------------------------------------------------------

    best_val = float("inf")
    patience = 0

    for epoch in range(1, EPOCHS + 1):
        start = time.time()

        lr = optimizer.param_groups[0]["lr"]

        print("\n" + "=" * 90)
        print(f"V4.1 EPOCH {epoch}/{EPOCHS} | LR = {lr:.8f}")
        print("=" * 90)

        train_metrics = run_epoch(
            model,
            train_loader,
            loss_fn,
            device,
            optimizer=optimizer,
            scaler=scaler,
        )

        val_metrics = run_epoch(
            model,
            val_loader,
            loss_fn,
            device,
        )

        scheduler.step(val_metrics["loss"])

        elapsed = (time.time() - start) / 60.0

        print(
            f"Train loss: {train_metrics['loss']:.4f} | "
            f"Small: {train_metrics['small']:.4f} | "
            f"Large: {train_metrics['large']:.4f}"
        )

        print(
            f"Val loss  : {val_metrics['loss']:.4f} | "
            f"Small: {val_metrics['small']:.4f} | "
            f"Large: {val_metrics['large']:.4f}"
        )

        train_total = max(1, train_metrics["samples"])

        print(
            "Train source mix: "
            f"BMD {100.0 * train_metrics['bmd'] / train_total:.2f}% | "
            f"Ambulance {100.0 * train_metrics['ambulance'] / train_total:.2f}%"
        )

        print("Collisions :", train_metrics["collisions"])
        print(f"Epoch time : {elapsed:.2f} min")

        # Always save last.
        torch.save(
            model.state_dict(),
            LAST_MODEL,
        )

        improved = val_metrics["loss"] < best_val - 1e-6

        if improved:
            best_val = val_metrics["loss"]
            patience = 0

            torch.save(
                model.state_dict(),
                BEST_MODEL,
            )

            print("✅ New V4.1 BEST model saved.")

        else:
            patience += 1
            print(
                f"No validation improvement "
                f"({patience}/{EARLY_STOPPING_PATIENCE})."
            )

        checkpoint = {
            "epoch": epoch,
            "model_state_dict": model.state_dict(),
            "optimizer_state_dict": optimizer.state_dict(),
            "scheduler_state_dict": scheduler.state_dict(),
            "scaler_state_dict": scaler.state_dict(),
            "best_val_loss": best_val,
            "patience": patience,
            "config": {
                "num_classes": NUM_CLASSES,
                "image_size": IMAGE_SIZE,
                "batch_size": BATCH_SIZE,
                "learning_rate": LEARNING_RATE,
                "lambda_box": LAMBDA_BOX,
                "lambda_obj": LAMBDA_OBJ,
                "lambda_noobj": LAMBDA_NOOBJ,
                "lambda_class": LAMBDA_CLASS,
                "start_model": str(START_MODEL),
            },
        }

        torch.save(
            checkpoint,
            CHECKPOINT,
        )

        if patience >= EARLY_STOPPING_PATIENCE:
            print("\nEarly stopping triggered.")
            break

    print("\n" + "=" * 90)
    print("✅ V4.1 FINE-TUNING COMPLETE")
    print(f"Best validation loss: {best_val:.6f}")
    print("Best model:", BEST_MODEL)
    print("=" * 90)
    print(
        "\nIMPORTANT: Do not replace V4 yet. "
        "Evaluate V4.1 on both BMD and ambulance validation first."
    )


if __name__ == "__main__":
    main()
