import torch
from torch.utils.data import DataLoader
from pathlib import Path

from model import TrafficCNN
from traffic_dataset import TrafficDataset
from target_generator import create_target_grid
from loss import TrafficDetectionLoss


# ==================================================
# SETTINGS
# ==================================================

NUM_CLASSES = 14
GRID_SIZE = 28
IMAGE_SIZE = 448

BATCH_SIZE = 4
EPOCHS = 20
LEARNING_RATE = 0.001

NUM_WORKERS = 0

EARLY_STOPPING_PATIENCE = 5


# ==================================================
# PATHS
# ==================================================

BASE_DIR = Path(__file__).parent.parent


TRAIN_IMAGE_DIR = (
    BASE_DIR
    / "dataset"
    / "train"
    / "images"
)

TRAIN_LABEL_DIR = (
    BASE_DIR
    / "dataset"
    / "train"
    / "labels"
)


VAL_IMAGE_DIR = (
    BASE_DIR
    / "dataset"
    / "val"
    / "images"
)

VAL_LABEL_DIR = (
    BASE_DIR
    / "dataset"
    / "val"
    / "labels"
)


# ==================================================
# V3 MODEL PATHS
# ==================================================

BEST_MODEL_PATH = (
    BASE_DIR
    / "traffic_detector_v3_best.pth"
)

LAST_MODEL_PATH = (
    BASE_DIR
    / "traffic_detector_v3_last.pth"
)

CHECKPOINT_PATH = (
    BASE_DIR
    / "traffic_detector_v3_checkpoint.pth"
)


# ==================================================
# DEVICE
# ==================================================

device = torch.device(
    "cuda"
    if torch.cuda.is_available()
    else "cpu"
)

print(
    "Using device:",
    device
)


if torch.cuda.is_available():

    print(
        "GPU:",
        torch.cuda.get_device_name(0)
    )

    # Optimizes convolution algorithms
    # for fixed 448 x 448 input size

    torch.backends.cudnn.benchmark = True


# ==================================================
# AMP
# ==================================================

AMP_ENABLED = (
    device.type == "cuda"
)

print(
    "AMP enabled:",
    AMP_ENABLED
)


# ==================================================
# DATASETS
# ==================================================

# --------------------------------------------------
# TRAIN DATASET
#
# Augmentation enabled
# --------------------------------------------------

train_dataset = TrafficDataset(
    TRAIN_IMAGE_DIR,
    TRAIN_LABEL_DIR,
    image_size=IMAGE_SIZE,
    augment=True
)


# --------------------------------------------------
# VALIDATION DATASET
#
# NO augmentation
# --------------------------------------------------

val_dataset = TrafficDataset(
    VAL_IMAGE_DIR,
    VAL_LABEL_DIR,
    image_size=IMAGE_SIZE,
    augment=False
)


print(
    "Training images:",
    len(train_dataset)
)

print(
    "Validation images:",
    len(val_dataset)
)


print(
    "Training augmentation:",
    train_dataset.augment
)

print(
    "Validation augmentation:",
    val_dataset.augment
)


# ==================================================
# COLLATE FUNCTION
# ==================================================

def collate_fn(batch):

    images = []
    targets = []

    for image, boxes, categories in batch:

        target = create_target_grid(
            boxes,
            categories,
            grid_size=GRID_SIZE,
            num_classes=NUM_CLASSES
        )

        images.append(
            image
        )

        targets.append(
            target
        )


    images = torch.stack(
        images
    )

    targets = torch.stack(
        targets
    )


    return (
        images,
        targets
    )


# ==================================================
# DATALOADERS
# ==================================================

train_loader = DataLoader(
    train_dataset,
    batch_size=BATCH_SIZE,
    shuffle=True,
    num_workers=NUM_WORKERS,
    pin_memory=torch.cuda.is_available(),
    collate_fn=collate_fn
)


val_loader = DataLoader(
    val_dataset,
    batch_size=BATCH_SIZE,
    shuffle=False,
    num_workers=NUM_WORKERS,
    pin_memory=torch.cuda.is_available(),
    collate_fn=collate_fn
)


# ==================================================
# MODEL
# ==================================================

model = TrafficCNN(
    num_classes=NUM_CLASSES
).to(
    device
)


# ==================================================
# LOSS
# ==================================================

criterion = (
    TrafficDetectionLoss()
    .to(device)
)


# ==================================================
# OPTIMIZER
# ==================================================

optimizer = torch.optim.AdamW(
    model.parameters(),
    lr=LEARNING_RATE,
    weight_decay=1e-4
)


# ==================================================
# LEARNING RATE SCHEDULER
# ==================================================

scheduler = (
    torch.optim.lr_scheduler
    .ReduceLROnPlateau(
        optimizer,
        mode="min",
        factor=0.5,
        patience=2
    )
)


# ==================================================
# AMP GRADIENT SCALER
# ==================================================

scaler = torch.amp.GradScaler(
    "cuda",
    enabled=AMP_ENABLED
)


# ==================================================
# TRAINING VARIABLES
# ==================================================

best_val_loss = float(
    "inf"
)

epochs_without_improvement = 0


# ==================================================
# TRAINING LOOP
# ==================================================

for epoch in range(
    1,
    EPOCHS + 1
):


    # ==================================================
    # TRAIN
    # ==================================================

    model.train()

    train_loss = 0.0


    for batch_index, (
        images,
        targets
    ) in enumerate(
        train_loader
    ):


        images = images.to(
            device,
            non_blocking=True
        )

        targets = targets.to(
            device,
            non_blocking=True
        )


        optimizer.zero_grad(
            set_to_none=True
        )


        # ==============================================
        # FORWARD PASS WITH AMP
        # ==============================================

        with torch.amp.autocast(
            device_type=device.type,
            dtype=torch.float16,
            enabled=AMP_ENABLED
        ):

            predictions = model(
                images
            )

            loss, loss_parts = criterion(
                predictions,
                targets
            )


        # ==============================================
        # BACKPROPAGATION
        # ==============================================

        scaler.scale(
            loss
        ).backward()


        # ----------------------------------------------
        # Unscale before gradient clipping
        # ----------------------------------------------

        scaler.unscale_(
            optimizer
        )


        torch.nn.utils.clip_grad_norm_(
            model.parameters(),
            max_norm=5.0
        )


        scaler.step(
            optimizer
        )

        scaler.update()


        train_loss += (
            loss.item()
        )


        # ==============================================
        # PROGRESS
        # ==============================================

        if (
            batch_index + 1
        ) % 100 == 0:

            print(
                f"Epoch "
                f"{epoch}/{EPOCHS} "
                f"| Batch "
                f"{batch_index + 1}/"
                f"{len(train_loader)} "
                f"| Loss "
                f"{loss.item():.4f}"
            )


    train_loss /= len(
        train_loader
    )


    # ==================================================
    # VALIDATION
    # ==================================================

    model.eval()

    val_loss = 0.0


    with torch.no_grad():

        for images, targets in (
            val_loader
        ):

            images = images.to(
                device,
                non_blocking=True
            )

            targets = targets.to(
                device,
                non_blocking=True
            )


            with torch.amp.autocast(
                device_type=device.type,
                dtype=torch.float16,
                enabled=AMP_ENABLED
            ):

                predictions = model(
                    images
                )

                loss, _ = criterion(
                    predictions,
                    targets
                )


            val_loss += (
                loss.item()
            )


    val_loss /= len(
        val_loader
    )


    # ==================================================
    # LEARNING RATE UPDATE
    # ==================================================

    scheduler.step(
        val_loss
    )


    current_lr = (
        optimizer
        .param_groups[0]["lr"]
    )


    # ==================================================
    # EPOCH SUMMARY
    # ==================================================

    print(
        "\n===================================="
    )

    print(
        f"Epoch {epoch}/{EPOCHS}"
    )

    print(
        f"Train Loss : "
        f"{train_loss:.4f}"
    )

    print(
        f"Val Loss   : "
        f"{val_loss:.4f}"
    )

    print(
        f"Learning Rate: "
        f"{current_lr:.6f}"
    )

    print(
        "====================================\n"
    )


    # ==================================================
    # BEST MODEL + EARLY STOPPING TRACKING
    # ==================================================

    if (
        val_loss
        <
        best_val_loss
    ):

        best_val_loss = (
            val_loss
        )

        epochs_without_improvement = 0


        torch.save(
            model.state_dict(),
            BEST_MODEL_PATH
        )


        print(
            "✅ Best V3 model saved!"
        )

        print(
            "Best validation loss:",
            f"{best_val_loss:.4f}"
        )


    else:

        epochs_without_improvement += 1


        print(
            "No validation improvement:",
            f"{epochs_without_improvement}/"
            f"{EARLY_STOPPING_PATIENCE}"
        )


    # ==================================================
    # SAVE LAST MODEL
    # ==================================================

    torch.save(
        model.state_dict(),
        LAST_MODEL_PATH
    )


    # ==================================================
    # SAVE FULL CHECKPOINT
    # ==================================================

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

            "train_loss":
                train_loss,

            "val_loss":
                val_loss,

            "epochs_without_improvement":
                epochs_without_improvement

        },

        CHECKPOINT_PATH
    )


    print(
        "💾 Full V3 checkpoint saved."
    )


    # ==================================================
    # EARLY STOPPING
    # ==================================================

    if (
        epochs_without_improvement
        >=
        EARLY_STOPPING_PATIENCE
    ):

        print(
            "\n🛑 Early stopping triggered."
        )

        print(
            "Validation loss did not improve "
            f"for "
            f"{EARLY_STOPPING_PATIENCE} "
            "epochs."
        )

        print(
            "Best validation loss:",
            f"{best_val_loss:.4f}"
        )

        break


# ==================================================
# FINISHED
# ==================================================

print(
    "\n===================================="
)

print(
    "V3 training complete!"
)

print(
    "===================================="
)


print(
    "\nBest validation loss:",
    f"{best_val_loss:.4f}"
)


print(
    "\nBest V3 model:"
)

print(
    BEST_MODEL_PATH
)


print(
    "\nLast V3 model:"
)

print(
    LAST_MODEL_PATH
)


print(
    "\nV3 checkpoint:"
)

print(
    CHECKPOINT_PATH
)