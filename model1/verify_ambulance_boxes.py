from pathlib import Path
import json
import random

from PIL import Image, ImageDraw, ImageFont


# ==========================================================
# SETTINGS
# ==========================================================

BASE_DIR = Path(__file__).parent.parent

TRAIN_DIR = (
    BASE_DIR
    / "ambulance_raw"
    / "train"
)

ANNOTATION_FILE = (
    TRAIN_DIR
    / "_annotations.coco.json"
)

OUTPUT_DIR = (
    BASE_DIR
    / "ambulance_box_check"
)

AMBULANCE_CATEGORY_ID = 3
NUM_SAMPLES = 12

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ==========================================================
# LOAD COCO
# ==========================================================

with open(
    ANNOTATION_FILE,
    "r",
    encoding="utf-8"
) as f:

    data = json.load(f)


images = {
    image["id"]: image
    for image in data["images"]
}


ambulance_annotations = [
    annotation
    for annotation in data["annotations"]
    if annotation["category_id"]
    == AMBULANCE_CATEGORY_ID
]


print("=" * 65)
print("AMBULANCE BOX VISUAL VERIFICATION")
print("=" * 65)

print(
    "Ambulance annotations:",
    len(ambulance_annotations)
)


# ==========================================================
# RANDOM SAMPLE
# ==========================================================

samples = random.sample(
    ambulance_annotations,
    min(
        NUM_SAMPLES,
        len(ambulance_annotations)
    )
)


# ==========================================================
# DRAW
# ==========================================================

for sample_number, annotation in enumerate(
    samples,
    start=1
):

    image_info = images[
        annotation["image_id"]
    ]

    image_path = (
        TRAIN_DIR
        / image_info["file_name"]
    )


    image = Image.open(
        image_path
    ).convert(
        "RGB"
    )


    draw = ImageDraw.Draw(
        image
    )


    x, y, w, h = annotation["bbox"]


    x2 = x + w
    y2 = y + h


    # Bounding box
    draw.rectangle(
        [
            x,
            y,
            x2,
            y2
        ],
        outline="red",
        width=5
    )


    # Label background
    label = "AMBULANCE"

    text_box = draw.textbbox(
        (x, y),
        label
    )


    text_height = (
        text_box[3]
        - text_box[1]
    )


    label_top = max(
        0,
        y - text_height - 8
    )


    draw.rectangle(
        [
            x,
            label_top,
            x + 110,
            y
        ],
        fill="red"
    )


    draw.text(
        (
            x + 4,
            label_top + 2
        ),
        label,
        fill="white"
    )


    # ======================================================
    # SAVE
    # ======================================================

    output_path = (
        OUTPUT_DIR
        / (
            f"ambulance_check_"
            f"{sample_number:02d}.jpg"
        )
    )


    image.save(
        output_path,
        quality=95
    )


    print(
        f"{sample_number:02d}: "
        f"{image_info['file_name']} "
        f"bbox="
        f"[{x:.1f}, {y:.1f}, "
        f"{w:.1f}, {h:.1f}]"
    )


print("\nSaved to:")
print(OUTPUT_DIR)

print("\n" + "=" * 65)
print("✅ VISUAL SAMPLES CREATED")
print("=" * 65)