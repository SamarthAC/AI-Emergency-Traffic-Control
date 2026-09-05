import random
import time
from pathlib import Path

import numpy as np
import torch
from torch.utils.data import Dataset, DataLoader, ConcatDataset

from traffic_dataset_v4 import TrafficDatasetV4
from target_generator_v4 import create_multiscale_targets_v4
from model_v4 import TrafficDetectorV4
from loss_v4 import MultiScaleTrafficLossV4


# ==========================================================
# CONFIG
# ==========================================================

BASE_DIR = Path(__file__).resolve().parent.parent
MODEL_DIR = Path(__file__).resolve().parent

NUM_CLASSES = 15
IMAGE_SIZE = 448

SEED = 42

EPOCHS = 30
BATCH_SIZE = 8
NUM_WORKERS = 4

LEARNING_RATE = 1e-3
WEIGHT_DECAY = 1e-4

GRAD_CLIP = 5.0

EARLY_STOPPING_PATIENCE = 6

RESUME = True


CLASS_WEIGHTS = [
    0.5167,
    0.6865,
    0.7775,
    1.0168,
    0.8197,
    0.9757,
    0.3778,
    0.2342,
    0.7230,
    2.5634,
    1.4951,
    1.4157,
    1.5117,
    0.0000,
    0.8861
]


# ==========================================================
# PATHS
# ==========================================================

BMD_TRAIN_IMAGES = BASE_DIR / "dataset_v4/train/images"
BMD_TRAIN_LABELS = BASE_DIR / "dataset_v4/train/labels"

BMD_VAL_IMAGES = BASE_DIR / "dataset_v4/val/images"
BMD_VAL_LABELS = BASE_DIR / "dataset_v4/val/labels"

AMB_TRAIN_IMAGES = BASE_DIR / "ambulance_v4/train/images"
AMB_TRAIN_LABELS = BASE_DIR / "ambulance_v4/train/labels"

AMB_VAL_IMAGES = BASE_DIR / "ambulance_v4/valid/images"
AMB_VAL_LABELS = BASE_DIR / "ambulance_v4/valid/labels"


BEST_MODEL_PATH = MODEL_DIR / "traffic_detector_v4_best.pth"
LAST_MODEL_PATH = MODEL_DIR / "traffic_detector_v4_last.pth"
CHECKPOINT_PATH = MODEL_DIR / "traffic_detector_v4_checkpoint.pth"


# ==========================================================
# SEED
# ==========================================================

def set_seed(seed):

    random.seed(seed)
    np.random.seed(seed)

    torch.manual_seed(seed)

    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


# ==========================================================
# ADD SOURCE INFORMATION
# ==========================================================

class SourceDataset(Dataset):

    def __init__(self, dataset, source):

        self.dataset = dataset
        self.source = source

    def __len__(self):

        return len(self.dataset)

    def __getitem__(self, index):

        image, boxes, categories, supervision = (
            self.dataset[index]
        )

        return (
            image,
            boxes,
            categories,
            supervision,
            self.source
        )


# ==========================================================
# COLLATE
# ==========================================================

def detection_collate(batch):

    images = []
    boxes = []
    categories = []
    supervision = []
    sources = []

    for sample in batch:

        (
            image,
            sample_boxes,
            sample_categories,
            sample_supervision,
            source
        ) = sample

        images.append(image)
        boxes.append(sample_boxes)
        categories.append(sample_categories)
        supervision.append(sample_supervision)
        sources.append(source)

    return (
        torch.stack(images),
        boxes,
        categories,
        supervision,
        sources
    )


# ==========================================================
# BUILD TARGETS
# ==========================================================

def build_target_batch(
    boxes_list,
    categories_list,
    supervision_list,
    device
):

    small_targets = []
    large_targets = []

    small_masks = []
    large_masks = []

    collisions = 0

    for boxes, categories, supervision in zip(
        boxes_list,
        categories_list,
        supervision_list
    ):

        result = create_multiscale_targets_v4(
            boxes,
            categories,
            supervision=supervision,
            num_classes=NUM_CLASSES,
            image_size=IMAGE_SIZE
        )

        small_targets.append(
            result["small_target"]
        )

        large_targets.append(
            result["large_target"]
        )

        small_masks.append(
            result["small_objectness_mask"]
        )

        large_masks.append(
            result["large_objectness_mask"]
        )

        collisions += (
            result["small_collisions"]
            + result["large_collisions"]
        )

    targets = {

        "small":
            torch.stack(
                small_targets
            ).to(
                device,
                non_blocking=True
            ),

        "large":
            torch.stack(
                large_targets
            ).to(
                device,
                non_blocking=True
            )
    }

    masks = {

        "small":
            torch.stack(
                small_masks
            ).to(
                device,
                non_blocking=True
            ),

        "large":
            torch.stack(
                large_masks
            ).to(
                device,
                non_blocking=True
            )
    }

    return targets, masks, collisions


# ==========================================================
# TRAIN ONE EPOCH
# ==========================================================

def train_one_epoch(
    model,
    loader,
    criterion,
    optimizer,
    scaler,
    device,
    epoch
):

    model.train()

    running_loss = 0.0
    small_loss = 0.0
    large_loss = 0.0

    total_collisions = 0

    bmd_count = 0
    ambulance_count = 0

    start_time = time.time()

    for batch_index, batch in enumerate(
        loader,
        start=1
    ):

        (
            images,
            boxes,
            categories,
            supervision,
            sources
        ) = batch

        bmd_count += sources.count("bmd")

        ambulance_count += sources.count(
            "ambulance"
        )

        images = images.to(
            device,
            non_blocking=True
        )

        targets, masks, collisions = (
            build_target_batch(
                boxes,
                categories,
                supervision,
                device
            )
        )

        total_collisions += collisions

        optimizer.zero_grad(
            set_to_none=True
        )

        with torch.amp.autocast(
            device_type=device.type,
            enabled=device.type == "cuda"
        ):

            predictions = model(images)

            losses = criterion(
                predictions,
                targets,
                objectness_masks=masks
            )

            loss = losses["total"]

        if not torch.isfinite(loss):

            raise RuntimeError(
                f"Non-finite loss at "
                f"batch {batch_index}"
            )

        scaler.scale(loss).backward()

        scaler.unscale_(optimizer)

        torch.nn.utils.clip_grad_norm_(
            model.parameters(),
            GRAD_CLIP
        )

        scaler.step(optimizer)
        scaler.update()

        running_loss += loss.item()

        small_loss += (
            losses["small_total"].item()
        )

        large_loss += (
            losses["large_total"].item()
        )

        if (
            batch_index == 1
            or batch_index % 100 == 0
            or batch_index == len(loader)
        ):

            print(
                f"Epoch {epoch:02d} "
                f"| Batch "
                f"{batch_index:04d}/"
                f"{len(loader):04d} "
                f"| Loss "
                f"{loss.item():.4f}"
            )

    batches = len(loader)

    return {

        "loss":
            running_loss / batches,

        "small":
            small_loss / batches,

        "large":
            large_loss / batches,

        "collisions":
            total_collisions,

        "bmd":
            bmd_count,

        "ambulance":
            ambulance_count,

        "seconds":
            time.time() - start_time
    }


# ==========================================================
# VALIDATION
# ==========================================================

@torch.no_grad()
def validate(
    model,
    loader,
    criterion,
    device
):

    model.eval()

    running_loss = 0.0
    small_loss = 0.0
    large_loss = 0.0

    total_collisions = 0

    for batch in loader:

        (
            images,
            boxes,
            categories,
            supervision,
            sources
        ) = batch

        images = images.to(
            device,
            non_blocking=True
        )

        targets, masks, collisions = (
            build_target_batch(
                boxes,
                categories,
                supervision,
                device
            )
        )

        total_collisions += collisions

        with torch.amp.autocast(
            device_type=device.type,
            enabled=device.type == "cuda"
        ):

            predictions = model(images)

            losses = criterion(
                predictions,
                targets,
                objectness_masks=masks
            )

        loss = losses["total"]

        if not torch.isfinite(loss):

            raise RuntimeError(
                "Non-finite validation loss."
            )

        running_loss += loss.item()

        small_loss += (
            losses["small_total"].item()
        )

        large_loss += (
            losses["large_total"].item()
        )

    batches = len(loader)

    return {

        "loss":
            running_loss / batches,

        "small":
            small_loss / batches,

        "large":
            large_loss / batches,

        "collisions":
            total_collisions
    }


# ==========================================================
# CHECKPOINT
# ==========================================================

def save_checkpoint(
    model,
    optimizer,
    scheduler,
    scaler,
    epoch,
    best_val_loss,
    patience_counter
):

    torch.save(
        {
            "epoch":
                epoch,

            "model_state_dict":
                model.state_dict(),

            "optimizer_state_dict":
                optimizer.state_dict(),

            "scheduler_state_dict":
                scheduler.state_dict(),

            "scaler_state_dict":
                scaler.state_dict(),

            "best_val_loss":
                best_val_loss,

            "patience_counter":
                patience_counter,

            "num_classes":
                NUM_CLASSES,

            "image_size":
                IMAGE_SIZE,

            "class_weights":
                CLASS_WEIGHTS
        },
        CHECKPOINT_PATH
    )


# ==========================================================
# MAIN
# ==========================================================

def main():

    print("=" * 80)
    print("V4 FULL TRAINING")
    print("=" * 80)

    set_seed(SEED)

    device = torch.device(
        "cuda"
        if torch.cuda.is_available()
        else "cpu"
    )

    print("Device:", device)

    if device.type == "cuda":

        print(
            "GPU:",
            torch.cuda.get_device_name(0)
        )

        torch.backends.cudnn.benchmark = True
        torch.backends.cuda.matmul.allow_tf32 = True
        torch.backends.cudnn.allow_tf32 = True
        torch.set_float32_matmul_precision("high")

    # ======================================================
    # DATASETS
    # ======================================================

    print("\nLoading datasets...")

    bmd_train = TrafficDatasetV4(
        BMD_TRAIN_IMAGES,
        BMD_TRAIN_LABELS,
        image_size=IMAGE_SIZE,
        augment=True
    )

    ambulance_train = TrafficDatasetV4(
        AMB_TRAIN_IMAGES,
        AMB_TRAIN_LABELS,
        image_size=IMAGE_SIZE,
        augment=True
    )

    bmd_val = TrafficDatasetV4(
        BMD_VAL_IMAGES,
        BMD_VAL_LABELS,
        image_size=IMAGE_SIZE,
        augment=False
    )

    ambulance_val = TrafficDatasetV4(
        AMB_VAL_IMAGES,
        AMB_VAL_LABELS,
        image_size=IMAGE_SIZE,
        augment=False
    )

    # ======================================================
    # SOURCE WRAPPERS
    # ======================================================

    bmd_train = SourceDataset(
        bmd_train,
        "bmd"
    )

    ambulance_train = SourceDataset(
        ambulance_train,
        "ambulance"
    )

    bmd_val = SourceDataset(
        bmd_val,
        "bmd"
    )

    ambulance_val = SourceDataset(
        ambulance_val,
        "ambulance"
    )

    # ======================================================
    # CONCATENATE
    # ======================================================

    train_dataset = ConcatDataset(
        [
            bmd_train,
            ambulance_train
        ]
    )

    val_dataset = ConcatDataset(
        [
            bmd_val,
            ambulance_val
        ]
    )

    print(
        "BMD train:",
        len(bmd_train)
    )

    print(
        "Ambulance train:",
        len(ambulance_train)
    )

    print(
        "Total train:",
        len(train_dataset)
    )

    print(
        "BMD val:",
        len(bmd_val)
    )

    print(
        "Ambulance val:",
        len(ambulance_val)
    )

    print(
        "Total val:",
        len(val_dataset)
    )

    print(
        f"Natural train mix: "
        f"BMD="
        f"{len(bmd_train)/len(train_dataset)*100:.2f}% "
        f"| Ambulance="
        f"{len(ambulance_train)/len(train_dataset)*100:.2f}%"
    )

    # ======================================================
    # LOADERS
    # ======================================================

    train_loader = DataLoader(
        train_dataset,

        batch_size=BATCH_SIZE,

        shuffle=True,

        num_workers=NUM_WORKERS,

        pin_memory=(
            device.type == "cuda"
        ),

        collate_fn=detection_collate,

        drop_last=False
    )

    val_loader = DataLoader(
        val_dataset,

        batch_size=BATCH_SIZE,

        shuffle=False,

        num_workers=NUM_WORKERS,

        pin_memory=(
            device.type == "cuda"
        ),

        collate_fn=detection_collate,

        drop_last=False
    )

    print(
        "Train batches:",
        len(train_loader)
    )

    print(
        "Val batches:",
        len(val_loader)
    )

    # ======================================================
    # MODEL
    # ======================================================

    model = TrafficDetectorV4(
        num_classes=NUM_CLASSES
    ).to(device)

    print(
        "Model parameters:",
        f"{sum(p.numel() for p in model.parameters()):,}"
    )

    # ======================================================
    # LOSS
    # ======================================================

    criterion = MultiScaleTrafficLossV4(

        num_classes=NUM_CLASSES,

        lambda_box=5.0,

        lambda_obj=1.0,

        lambda_noobj=0.50,

        lambda_class=1.0,

        class_weights=CLASS_WEIGHTS,

        small_scale_weight=1.0,

        large_scale_weight=1.0

    ).to(device)

    # ======================================================
    # OPTIMIZER
    # ======================================================

    optimizer = torch.optim.AdamW(

        model.parameters(),

        lr=LEARNING_RATE,

        weight_decay=WEIGHT_DECAY
    )

    # ======================================================
    # SCHEDULER
    # ======================================================

    scheduler = (
        torch.optim.lr_scheduler.ReduceLROnPlateau(

            optimizer,

            mode="min",

            factor=0.5,

            patience=2,

            min_lr=1e-6
        )
    )

    # ======================================================
    # AMP
    # ======================================================

    scaler = torch.amp.GradScaler(

        device.type,

        enabled=device.type == "cuda"
    )

    # ======================================================
    # RESUME
    # ======================================================

    start_epoch = 1

    best_val_loss = float("inf")

    patience_counter = 0

    if RESUME and CHECKPOINT_PATH.exists():

        print(
            "\nLoading checkpoint..."
        )

        checkpoint = torch.load(
            CHECKPOINT_PATH,
            map_location=device
        )

        model.load_state_dict(
            checkpoint[
                "model_state_dict"
            ]
        )

        optimizer.load_state_dict(
            checkpoint[
                "optimizer_state_dict"
            ]
        )

        scheduler.load_state_dict(
            checkpoint[
                "scheduler_state_dict"
            ]
        )

        scaler.load_state_dict(
            checkpoint[
                "scaler_state_dict"
            ]
        )

        start_epoch = (
            checkpoint["epoch"] + 1
        )

        best_val_loss = checkpoint[
            "best_val_loss"
        ]

        patience_counter = checkpoint.get(
            "patience_counter",
            0
        )

        print(
            "Resuming from epoch:",
            start_epoch
        )

        print(
            "Best validation loss:",
            best_val_loss
        )

    # ======================================================
    # TRAIN
    # ======================================================

    print()
    print("=" * 80)
    print("STARTING FULL TRAINING")
    print("=" * 80)

    for epoch in range(
        start_epoch,
        EPOCHS + 1
    ):

        print()
        print("-" * 80)

        print(
            f"EPOCH {epoch}/{EPOCHS}"
        )

        print(
            "Learning rate:",
            f"{optimizer.param_groups[0]['lr']:.8f}"
        )

        train_stats = train_one_epoch(

            model,
            train_loader,
            criterion,
            optimizer,
            scaler,
            device,
            epoch
        )

        val_stats = validate(

            model,
            val_loader,
            criterion,
            device
        )

        scheduler.step(
            val_stats["loss"]
        )

        # ==================================================
        # SUMMARY
        # ==================================================

        total_seen = (
            train_stats["bmd"]
            + train_stats["ambulance"]
        )

        print()

        print(
            f"Train loss : "
            f"{train_stats['loss']:.4f}"
        )

        print(
            f"  Small    : "
            f"{train_stats['small']:.4f}"
        )

        print(
            f"  Large    : "
            f"{train_stats['large']:.4f}"
        )

        print(
            f"Val loss   : "
            f"{val_stats['loss']:.4f}"
        )

        print(
            f"  Small    : "
            f"{val_stats['small']:.4f}"
        )

        print(
            f"  Large    : "
            f"{val_stats['large']:.4f}"
        )

        print(
            "Samples seen:",
            total_seen
        )

        print(
            f"Source mix: "
            f"BMD="
            f"{train_stats['bmd']/total_seen*100:.2f}% "
            f"| Ambulance="
            f"{train_stats['ambulance']/total_seen*100:.2f}%"
        )

        print(
            "Target collisions:",
            train_stats["collisions"]
        )

        print(
            "Epoch time:",
            f"{train_stats['seconds']/60:.2f} min"
        )

        # ==================================================
        # SAVE LAST
        # ==================================================

        torch.save(
            model.state_dict(),
            LAST_MODEL_PATH
        )

        # ==================================================
        # BEST MODEL
        # ==================================================

        if val_stats["loss"] < best_val_loss:

            best_val_loss = (
                val_stats["loss"]
            )

            patience_counter = 0

            torch.save(
                model.state_dict(),
                BEST_MODEL_PATH
            )

            print(
                "✅ New BEST V4 model saved."
            )

        else:

            patience_counter += 1

            print(
                f"No improvement: "
                f"{patience_counter}/"
                f"{EARLY_STOPPING_PATIENCE}"
            )

        # ==================================================
        # CHECKPOINT
        # ==================================================

        save_checkpoint(
            model,
            optimizer,
            scheduler,
            scaler,
            epoch,
            best_val_loss,
            patience_counter
        )

        print(
            "Checkpoint saved."
        )

        # ==================================================
        # EARLY STOPPING
        # ==================================================

        if (
            patience_counter
            >= EARLY_STOPPING_PATIENCE
        ):

            print()
            print(
                "Early stopping triggered."
            )

            break

    # ======================================================
    # COMPLETE
    # ======================================================

    print()
    print("=" * 80)

    print(
        "✅ V4 FULL TRAINING COMPLETE"
    )

    print(
        "Best validation loss:",
        f"{best_val_loss:.6f}"
    )

    print(
        "Best model:",
        BEST_MODEL_PATH
    )

    print("=" * 80)


if __name__ == "__main__":
    main()