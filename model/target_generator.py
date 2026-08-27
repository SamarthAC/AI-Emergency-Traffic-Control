import torch


def create_target_grid(boxes, categories, grid_size=28, num_classes=14):

    # 19 = objectness + 4 bbox values + 14 classes
    target = torch.zeros(
        (5 + num_classes, grid_size, grid_size),
        dtype=torch.float32
    )

    for box, category in zip(boxes, categories):

        x, y, width, height = box.tolist()
        category = int(category.item())

        # Find centre of bounding box
        center_x = x + width / 2
        center_y = y + height / 2

        # Find responsible grid cell
        grid_x = min(int(center_x * grid_size), grid_size - 1)
        grid_y = min(int(center_y * grid_size), grid_size - 1)

        # Position relative to that grid cell
        cell_x = center_x * grid_size - grid_x
        cell_y = center_y * grid_size - grid_y

        # Object exists
        target[0, grid_y, grid_x] = 1.0

        # Bounding box
        target[1, grid_y, grid_x] = cell_x
        target[2, grid_y, grid_x] = cell_y
        target[3, grid_y, grid_x] = width
        target[4, grid_y, grid_x] = height

        # Class
        target[5 + category, grid_y, grid_x] = 1.0

    return target


# -----------------------------
# SIMPLE TEST
# -----------------------------

if __name__ == "__main__":

    boxes = torch.tensor([
        [0.8311, 0.4141, 0.1063, 0.2713],
        [0.3833, 0.1404, 0.0635, 0.0981],
        [0.7356, 0.7910, 0.2089, 0.2083],
        [0.3669, 0.1565, 0.0448, 0.0944]
    ])

    categories = torch.tensor([6, 7, 11, 11])

    target = create_target_grid(
        boxes,
        categories
    )

    print("Target shape:")
    print(target.shape)

    print("\nNumber of occupied cells:")
    print(int(target[0].sum().item()))

    print("\nOccupied grid cells:")

    positions = torch.nonzero(target[0])

    for grid_y, grid_x in positions:

        grid_y = int(grid_y)
        grid_x = int(grid_x)

        objectness = target[0, grid_y, grid_x]

        bbox = target[
            1:5,
            grid_y,
            grid_x
        ]

        class_values = target[
            5:,
            grid_y,
            grid_x
        ]

        class_id = torch.argmax(class_values).item()

        print(
            f"\nCell ({grid_x}, {grid_y})"
            f"\n  Object: {objectness.item()}"
            f"\n  Box: {bbox.tolist()}"
            f"\n  Class: {class_id}"
        )