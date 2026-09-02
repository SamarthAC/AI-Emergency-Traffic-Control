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
    / "ambulance_audit"
)

AMBULANCE_CATEGORY_ID = 3

NUM_SAMPLES = 100
IMAGES_PER_SHEET = 10

THUMBNAIL_SIZE = 320

# Fixed seed so results are reproducible
RANDOM_SEED = 42


# ==========================================================
# SETUP
# ==========================================================

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)

random.seed(
    RANDOM_SEED
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


image_map = {
    image["id"]: image
    for image in data["images"]
}


ambulance_annotations = [
    annotation
    for annotation in data["annotations"]
    if annotation["category_id"]
    == AMBULANCE_CATEGORY_ID
]


print("=" * 70)
print("AMBULANCE ANNOTATION AUDIT")
print("=" * 70)

print(
    "Available ambulance annotations:",
    len(ambulance_annotations)
)


# ==========================================================
# RANDOM SAMPLE
# ==========================================================

sample_count = min(
    NUM_SAMPLES,
    len(ambulance_annotations)
)


samples = random.sample(
    ambulance_annotations,
    sample_count
)


# ==========================================================
# PROCESS EACH SAMPLE
# ==========================================================

processed_images = []


for audit_number, annotation in enumerate(
    samples,
    start=1
):

    image_info = image_map[
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


    # ------------------------------------------------------
    # DRAW ORIGINAL BBOX
    # ------------------------------------------------------

    draw = ImageDraw.Draw(
        image
    )


    x, y, w, h = annotation["bbox"]

    draw.rectangle(
        [
            x,
            y,
            x + w,
            y + h
        ],
        outline="red",
        width=5
    )


    # ------------------------------------------------------
    # RESIZE WHILE PRESERVING ASPECT RATIO
    # ------------------------------------------------------

    image.thumbnail(
        (
            THUMBNAIL_SIZE,
            THUMBNAIL_SIZE
        )
    )


    # ------------------------------------------------------
    # CREATE TILE
    # ------------------------------------------------------

    tile_width = THUMBNAIL_SIZE
    tile_height = THUMBNAIL_SIZE + 40


    tile = Image.new(
        "RGB",
        (
            tile_width,
            tile_height
        ),
        "white"
    )


    # Center image
    paste_x = (
        tile_width
        - image.width
    ) // 2

    paste_y = (
        THUMBNAIL_SIZE
        - image.height
    ) // 2


    tile.paste(
        image,
        (
            paste_x,
            paste_y
        )
    )


    tile_draw = ImageDraw.Draw(
        tile
    )


    label = (
        f"#{audit_number:03d}"
    )


    tile_draw.text(
        (
            10,
            THUMBNAIL_SIZE + 10
        ),
        label,
        fill="black"
    )


    processed_images.append(
        tile
    )


# ==========================================================
# CREATE CONTACT SHEETS
# ==========================================================

sheet_number = 1


for start in range(
    0,
    len(processed_images),
    IMAGES_PER_SHEET
):

    batch = processed_images[
        start:
        start + IMAGES_PER_SHEET
    ]


    # 2 columns x 5 rows
    columns = 2
    rows = 5


    sheet_width = (
        columns
        * THUMBNAIL_SIZE
    )

    sheet_height = (
        rows
        * (
            THUMBNAIL_SIZE
            + 40
        )
    )


    sheet = Image.new(
        "RGB",
        (
            sheet_width,
            sheet_height
        ),
        "white"
    )


    for index, tile in enumerate(
        batch
    ):

        row = (
            index // columns
        )

        column = (
            index % columns
        )


        x = (
            column
            * THUMBNAIL_SIZE
        )

        y = (
            row
            * (
                THUMBNAIL_SIZE
                + 40
            )
        )


        sheet.paste(
            tile,
            (
                x,
                y
            )
        )


    output_path = (
        OUTPUT_DIR
        / f"audit_sheet_{sheet_number:02d}.jpg"
    )


    sheet.save(
        output_path,
        quality=95
    )


    print(
        "Created:",
        output_path.name
    )


    sheet_number += 1


# ==========================================================
# SAVE AUDIT INDEX
# ==========================================================

index_file = (
    OUTPUT_DIR
    / "audit_index.txt"
)


with open(
    index_file,
    "w",
    encoding="utf-8"
) as f:

    for audit_number, annotation in enumerate(
        samples,
        start=1
    ):

        image_info = image_map[
            annotation["image_id"]
        ]

        f.write(
            f"{audit_number:03d} | "
            f"annotation_id={annotation['id']} | "
            f"image={image_info['file_name']} | "
            f"bbox={annotation['bbox']}\n"
        )


print("\n" + "=" * 70)

print(
    f"Audit samples created: "
    f"{len(processed_images)}"
)

print(
    f"Contact sheets created: "
    f"{sheet_number - 1}"
)

print(
    "Output folder:"
)

print(
    OUTPUT_DIR
)

print("\n✅ AMBULANCE AUDIT CREATED!")

print("=" * 70)