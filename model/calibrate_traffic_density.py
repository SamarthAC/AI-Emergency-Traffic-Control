from pathlib import Path
import argparse
import json
import csv

from traffic_density import (
    calculate_traffic_density,
    load_inference_json,
)


def process_folder(folder_path):
    folder = Path(folder_path)

    if not folder.exists():
        raise FileNotFoundError(folder)

    json_files = sorted(
        folder.glob("*.json")
    )

    results = []

    for json_file in json_files:

        try:
            inference_result = load_inference_json(
                json_file
            )

            density_result = calculate_traffic_density(
                inference_result
            )

            results.append(
                {
                    "file": json_file.name,
                    "vehicle_count":
                        density_result["vehicle_count"],
                    "weighted_count":
                        density_result["weighted_vehicle_count"],
                    "occupancy_ratio":
                        density_result["occupancy_ratio"],
                    "average_confidence":
                        density_result["average_confidence"],
                    "traffic_score":
                        density_result["traffic_score"],
                    "traffic_level":
                        density_result["traffic_level"],
                    "ambulance":
                        density_result["ambulance_detected"],
                }
            )

        except Exception as error:

            print(
                f"Failed: {json_file.name}"
            )

            print(
                error
            )

    return results


def print_results(results):

    print()
    print("=" * 110)

    print(
        f"{'FILE':<30}"
        f"{'COUNT':>8}"
        f"{'WEIGHTED':>12}"
        f"{'OCCUPANCY':>12}"
        f"{'AVG CONF':>12}"
        f"{'SCORE':>10}"
        f"{'LEVEL':>10}"
    )

    print("=" * 110)

    for row in results:

        print(
            f"{row['file']:<30}"
            f"{row['vehicle_count']:>8}"
            f"{row['weighted_count']:>12.2f}"
            f"{row['occupancy_ratio'] * 100:>11.2f}%"
            f"{row['average_confidence']:>12.2f}"
            f"{row['traffic_score']:>10.2f}"
            f"{row['traffic_level']:>10}"
        )

    print("=" * 110)


def save_csv(results, output_path):

    fieldnames = [
        "file",
        "vehicle_count",
        "weighted_count",
        "occupancy_ratio",
        "average_confidence",
        "traffic_score",
        "traffic_level",
        "ambulance",
    ]

    with open(
        output_path,
        "w",
        newline="",
        encoding="utf-8",
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames,
        )

        writer.writeheader()

        writer.writerows(
            results
        )


def main():

    parser = argparse.ArgumentParser(
        description=(
            "Calibrate traffic density using "
            "multiple inference JSON files."
        )
    )

    parser.add_argument(
        "folder",
        help=(
            "Folder containing inference JSON files"
        ),
    )

    parser.add_argument(
        "--save",
        default="traffic_density_calibration.csv",
        help="CSV output path",
    )

    args = parser.parse_args()

    results = process_folder(
        args.folder
    )

    if not results:

        print(
            "No usable JSON files found."
        )

        return

    print_results(
        results
    )

    save_csv(
        results,
        args.save,
    )

    print()
    print(
        f"Saved calibration CSV: {args.save}"
    )


if __name__ == "__main__":
    main()