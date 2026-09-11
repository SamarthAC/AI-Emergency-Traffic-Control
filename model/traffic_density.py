import json
import argparse
from pathlib import Path


# ============================================================
# CONFIGURATION
# ============================================================

# These are INITIAL calibration values.
# We will tune them using low / medium / high traffic images.
COUNT_CAPACITY = 25.0
OCCUPANCY_CAPACITY = 0.45
GRID_COVERAGE_CAPACITY = 0.75

COUNT_WEIGHT = 0.45
OCCUPANCY_WEIGHT = 0.30
GRID_WEIGHT = 0.25

MIN_ROI_BOX_FRACTION = 0.50
GRID_COLUMNS = 4
GRID_ROWS = 3

# Initial traffic-level boundaries.
# These will also be calibrated later.
LOW_THRESHOLD = 48.0
HIGH_THRESHOLD = 90.0

# Default Road Region Of Interest (ROI)
#
# Format:
# x1, y1, x2, y2
#
# These are NORMALIZED coordinates.
#
# (0.0, 0.25, 1.0, 1.0)
# means:
# full image width
# ignore approximately top 25% of image
#
# IMPORTANT:
# This is only a starting ROI.
# Later each SUMO edge / camera can have its own ROI.
DEFAULT_ROI = (0.0, 0.25, 1.0, 1.0)


# ============================================================
# BASIC HELPERS
# ============================================================

def clamp(value, minimum, maximum):
    """
    Restrict value between minimum and maximum.
    """

    return max(
        minimum,
        min(value, maximum)
    )


def box_area(box):
    """
    Calculate area of a bounding box.

    Box format:
    [x1, y1, x2, y2]
    """

    x1, y1, x2, y2 = box

    width = max(
        0.0,
        x2 - x1
    )

    height = max(
        0.0,
        y2 - y1
    )

    return width * height


# ============================================================
# ROI
# ============================================================

def normalized_roi_to_pixels(
    roi,
    image_width,
    image_height
):
    """
    Convert normalized ROI coordinates into pixel coordinates.

    Example:

    normalized:
    (0.0, 0.25, 1.0, 1.0)

    becomes approximately:

    (0, 180, 1280, 720)

    for a 1280x720 image.
    """

    x1, y1, x2, y2 = roi

    x1 = clamp(x1, 0.0, 1.0)
    y1 = clamp(y1, 0.0, 1.0)
    x2 = clamp(x2, 0.0, 1.0)
    y2 = clamp(y2, 0.0, 1.0)

    return (
        x1 * image_width,
        y1 * image_height,
        x2 * image_width,
        y2 * image_height
    )


def intersection_box(
    box,
    roi_box
):
    """
    Return the part of a detection box that lies inside the ROI.

    Returns None if there is no intersection.
    """

    x1 = max(
        box[0],
        roi_box[0]
    )

    y1 = max(
        box[1],
        roi_box[1]
    )

    x2 = min(
        box[2],
        roi_box[2]
    )

    y2 = min(
        box[3],
        roi_box[3]
    )

    if x2 <= x1 or y2 <= y1:
        return None

    return [
        x1,
        y1,
        x2,
        y2
    ]




def box_center(box):
    """Return center point of [x1, y1, x2, y2]."""
    x1, y1, x2, y2 = box
    return ((x1 + x2) / 2.0, (y1 + y2) / 2.0)


def roi_intersection_fraction(box, roi_box):
    """Return fraction of original detection box inside ROI and clipped box."""
    original_area = box_area(box)
    if original_area <= 0:
        return 0.0, None

    clipped_box = intersection_box(box, roi_box)
    if clipped_box is None:
        return 0.0, None

    fraction = box_area(clipped_box) / original_area
    return clamp(fraction, 0.0, 1.0), clipped_box


def calculate_grid_coverage(boxes, roi_box, columns=GRID_COLUMNS, rows=GRID_ROWS):
    """
    Divide ROI into a grid and measure how many cells contain vehicle centers.
    Center-based coverage is less sensitive to oversized bounding boxes.
    """
    if columns <= 0 or rows <= 0:
        raise ValueError("Grid rows and columns must be greater than zero.")

    rx1, ry1, rx2, ry2 = roi_box
    rw = rx2 - rx1
    rh = ry2 - ry1
    if rw <= 0 or rh <= 0:
        raise ValueError("ROI dimensions must be greater than zero.")

    occupied = set()
    for box in boxes:
        cx, cy = box_center(box)
        nx = clamp((cx - rx1) / rw, 0.0, 0.999999)
        ny = clamp((cy - ry1) / rh, 0.0, 0.999999)
        col = int(nx * columns)
        row = int(ny * rows)
        occupied.add((row, col))

    total = columns * rows
    return {
        "occupied_grid_cells": len(occupied),
        "total_grid_cells": total,
        "grid_coverage_ratio": len(occupied) / total,
        "occupied_grid_coordinates": sorted([[r, c] for r, c in occupied]),
    }


# ============================================================
# UNION AREA
# ============================================================

def rectangle_union_area(
    boxes
):
    """
    Calculate the UNION area of multiple rectangles.

    This prevents overlapping detections from being
    double-counted when calculating road occupancy.

    Uses an x-axis sweep method.
    """

    if not boxes:
        return 0.0

    x_coordinates = set()

    for box in boxes:

        x1, _, x2, _ = box

        x_coordinates.add(
            float(x1)
        )

        x_coordinates.add(
            float(x2)
        )

    x_coordinates = sorted(
        x_coordinates
    )

    total_area = 0.0

    # --------------------------------------------------------
    # Process each vertical strip
    # --------------------------------------------------------

    for index in range(
        len(x_coordinates) - 1
    ):

        strip_x1 = x_coordinates[index]
        strip_x2 = x_coordinates[index + 1]

        strip_width = (
            strip_x2 - strip_x1
        )

        if strip_width <= 0:
            continue

        y_intervals = []

        # ----------------------------------------------------
        # Find rectangles crossing this strip
        # ----------------------------------------------------

        for box in boxes:

            x1, y1, x2, y2 = box

            if (
                x1 < strip_x2
                and
                x2 > strip_x1
            ):

                y_intervals.append(
                    (
                        float(y1),
                        float(y2)
                    )
                )

        if not y_intervals:
            continue

        # ----------------------------------------------------
        # Merge overlapping Y intervals
        # ----------------------------------------------------

        y_intervals.sort(
            key=lambda interval:
                interval[0]
        )

        merged_height = 0.0

        current_start = (
            y_intervals[0][0]
        )

        current_end = (
            y_intervals[0][1]
        )

        for start, end in y_intervals[1:]:

            if start <= current_end:

                current_end = max(
                    current_end,
                    end
                )

            else:

                merged_height += (
                    current_end
                    -
                    current_start
                )

                current_start = start
                current_end = end

        merged_height += (
            current_end
            -
            current_start
        )

        total_area += (
            strip_width
            *
            merged_height
        )

    return total_area


# ============================================================
# TRAFFIC LEVEL
# ============================================================

def get_traffic_level(
    traffic_score
):
    """
    Convert 0-100 traffic score into a simple category.
    """

    if traffic_score < LOW_THRESHOLD:
        return "LOW"

    if traffic_score < HIGH_THRESHOLD:
        return "MEDIUM"

    return "HIGH"


# ============================================================
# MAIN TRAFFIC DENSITY CALCULATION
# ============================================================

def calculate_traffic_density(
    inference_result,
    roi=DEFAULT_ROI
):
    """
    Convert V4 inference output into traffic-density information.

    Uses three signals:
    1. confidence-weighted vehicle count
    2. union bounding-box occupancy inside the road ROI
    3. spatial grid coverage inside the road ROI

    Ambulances are excluded from congestion calculation.
    """

    image_width = int(inference_result["image_width"])
    image_height = int(inference_result["image_height"])
    detections = inference_result.get("detections", [])

    roi_pixels = normalized_roi_to_pixels(roi, image_width, image_height)
    roi_area = box_area(roi_pixels)
    if roi_area <= 0:
        raise ValueError("ROI area must be greater than zero.")

    vehicle_boxes = []
    confidences = []
    roi_fractions = []
    weighted_vehicle_count = 0.0

    rejected_outside_roi = 0
    rejected_low_roi_fraction = 0
    ignored_ambulances = 0
    ignored_invalid_boxes = 0

    for detection in detections:
        class_name = str(detection.get("class_name", ""))
        class_id = detection.get("class_id")
        confidence = float(detection.get("confidence", 0.0))
        box = detection.get("box_pixels")

        if box is None or len(box) != 4:
            ignored_invalid_boxes += 1
            continue

        box = [float(v) for v in box]
        if box_area(box) <= 0:
            ignored_invalid_boxes += 1
            continue

        if class_name.lower() == "ambulance" or class_id == 14:
            ignored_ambulances += 1
            continue

        roi_fraction, clipped_box = roi_intersection_fraction(box, roi_pixels)
        if clipped_box is None:
            rejected_outside_roi += 1
            continue

        if roi_fraction < MIN_ROI_BOX_FRACTION:
            rejected_low_roi_fraction += 1
            continue

        vehicle_boxes.append(clipped_box)
        confidences.append(confidence)
        roi_fractions.append(roi_fraction)
        weighted_vehicle_count += confidence

    vehicle_count = len(vehicle_boxes)
    average_confidence = (sum(confidences) / len(confidences)) if confidences else 0.0
    average_roi_fraction = (sum(roi_fractions) / len(roi_fractions)) if roi_fractions else 0.0

    occupied_area = rectangle_union_area(vehicle_boxes)
    occupancy_ratio = clamp(occupied_area / roi_area, 0.0, 1.0)

    grid_result = calculate_grid_coverage(vehicle_boxes, roi_pixels)
    grid_coverage_ratio = grid_result["grid_coverage_ratio"]

    count_component = clamp(weighted_vehicle_count / COUNT_CAPACITY, 0.0, 1.0)
    occupancy_component = clamp(occupancy_ratio / OCCUPANCY_CAPACITY, 0.0, 1.0)
    grid_component = clamp(grid_coverage_ratio / GRID_COVERAGE_CAPACITY, 0.0, 1.0)

    traffic_score = 100.0 * (
        COUNT_WEIGHT * count_component
        + OCCUPANCY_WEIGHT * occupancy_component
        + GRID_WEIGHT * grid_component
    )
    traffic_score = clamp(traffic_score, 0.0, 100.0)
    traffic_level = get_traffic_level(traffic_score)

    return {
        "vehicle_count": vehicle_count,
        "weighted_vehicle_count": round(weighted_vehicle_count, 4),
        "occupied_area_pixels": round(occupied_area, 2),
        "roi_area_pixels": round(roi_area, 2),
        "occupancy_ratio": round(occupancy_ratio, 4),
        "average_confidence": round(average_confidence, 4),
        "average_roi_fraction": round(average_roi_fraction, 4),
        "count_component": round(count_component, 4),
        "occupancy_component": round(occupancy_component, 4),
        "grid_coverage_ratio": round(grid_coverage_ratio, 4),
        "grid_component": round(grid_component, 4),
        "occupied_grid_cells": grid_result["occupied_grid_cells"],
        "total_grid_cells": grid_result["total_grid_cells"],
        "occupied_grid_coordinates": grid_result["occupied_grid_coordinates"],
        "traffic_score": round(traffic_score, 2),
        "traffic_level": traffic_level,
        "ambulance_detected": bool(inference_result.get("ambulance_detected", False)),
        "ignored_ambulance_detections": ignored_ambulances,
        "rejected_outside_roi": rejected_outside_roi,
        "rejected_low_roi_fraction": rejected_low_roi_fraction,
        "ignored_invalid_boxes": ignored_invalid_boxes,
        "min_roi_box_fraction": MIN_ROI_BOX_FRACTION,
        "roi_normalized": list(roi),
        "roi_pixels": [round(value, 2) for value in roi_pixels],
        "configuration": {
            "count_capacity": COUNT_CAPACITY,
            "occupancy_capacity": OCCUPANCY_CAPACITY,
            "grid_coverage_capacity": GRID_COVERAGE_CAPACITY,
            "count_weight": COUNT_WEIGHT,
            "occupancy_weight": OCCUPANCY_WEIGHT,
            "grid_weight": GRID_WEIGHT,
            "low_threshold": LOW_THRESHOLD,
            "high_threshold": HIGH_THRESHOLD,
            "grid_columns": GRID_COLUMNS,
            "grid_rows": GRID_ROWS,
        },
    }


# ============================================================
# LOAD INFERENCE JSON
# ============================================================

def load_inference_json(
    json_path
):
    """
    Load JSON produced by inference_v4.py.
    """

    json_path = Path(
        json_path
    )

    if not json_path.exists():

        raise FileNotFoundError(
            f"JSON file not found: "
            f"{json_path}"
        )

    with open(
        json_path,
        "r",
        encoding="utf-8"
    ) as file:

        return json.load(
            file
        )


# ============================================================
# COMMAND LINE
# ============================================================

def main():

    parser = argparse.ArgumentParser(
        description=(
            "Calculate traffic density "
            "from V4 inference JSON."
        )
    )

    parser.add_argument(
        "json_path",
        help=(
            "Path to JSON generated "
            "by inference_v4.py"
        )
    )

    parser.add_argument(
        "--roi",
        nargs=4,
        type=float,
        metavar=(
            "X1",
            "Y1",
            "X2",
            "Y2"
        ),
        default=DEFAULT_ROI,
        help=(
            "Normalized road ROI. "
            "Example: "
            "--roi 0 0.25 1 1"
        )
    )

    parser.add_argument(
        "--save",
        type=str,
        default=None,
        help=(
            "Optional path for saving "
            "traffic-density JSON."
        )
    )

    args = parser.parse_args()

    inference_result = (
        load_inference_json(
            args.json_path
        )
    )

    roi = tuple(
        args.roi
    )

    density_result = (
        calculate_traffic_density(
            inference_result,
            roi=roi
        )
    )

    print(
        "\n"
        +
        "=" * 60
    )

    print(
        "TRAFFIC DENSITY RESULT"
    )

    print(
        "=" * 60
    )

    print(
        json.dumps(
            density_result,
            indent=4
        )
    )

    print(
        "=" * 60
    )

    # --------------------------------------------------------
    # Save optional JSON
    # --------------------------------------------------------

    if args.save is not None:

        save_path = Path(
            args.save
        )

        with open(
            save_path,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                density_result,
                file,
                indent=4
            )

        print(
            f"\nSaved density result to: "
            f"{save_path}"
        )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()