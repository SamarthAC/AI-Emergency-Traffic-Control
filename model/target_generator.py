import torch


def create_target_grid(
    boxes,
    categories,
    grid_size=28,
    num_classes=14
):

    # ==================================================
    # TARGET FORMAT
    # ==================================================
    #
    # Channel 0      : Objectness
    # Channels 1-4   : Bounding box
    # Channels 5+    : Class probabilities
    #
    # Total:
    #
    # 1 + 4 + 14 = 19 channels
    # ==================================================

    target = torch.zeros(
        (
            5 + num_classes,
            grid_size,
            grid_size
        ),
        dtype=torch.float32
    )


    # ==================================================
    # STORE AREA OF OBJECT CURRENTLY ASSIGNED
    # TO EACH GRID CELL
    # ==================================================
    #
    # Our detector predicts ONE object per grid cell.
    #
    # If multiple objects have centres inside the same
    # cell, we keep the larger object.
    #
    # This avoids random annotation-order overwriting.
    # ==================================================

    assigned_area = torch.zeros(
        (
            grid_size,
            grid_size
        ),
        dtype=torch.float32
    )


    # ==================================================
    # PROCESS OBJECTS
    # ==================================================

    for box, category in zip(
        boxes,
        categories
    ):

        x, y, width, height = (
            box.tolist()
        )

        category = int(
            category.item()
        )


        # ==================================================
        # SAFETY CHECKS
        # ==================================================

        if (
            width <= 0
            or
            height <= 0
        ):
            continue


        if (
            category < 0
            or
            category >= num_classes
        ):
            continue


        # ==================================================
        # BOX CENTRE
        # ==================================================

        center_x = (
            x
            +
            width / 2
        )

        center_y = (
            y
            +
            height / 2
        )


        # Clamp because floating-point values can
        # occasionally reach the boundary.

        center_x = max(
            0.0,
            min(
                center_x,
                1.0 - 1e-6
            )
        )

        center_y = max(
            0.0,
            min(
                center_y,
                1.0 - 1e-6
            )
        )


        # ==================================================
        # RESPONSIBLE GRID CELL
        # ==================================================

        grid_x = int(
            center_x
            *
            grid_size
        )

        grid_y = int(
            center_y
            *
            grid_size
        )


        # ==================================================
        # OBJECT AREA
        # ==================================================

        object_area = (
            width
            *
            height
        )


        # ==================================================
        # COLLISION HANDLING
        # ==================================================
        #
        # If this cell already contains an object,
        # only replace it when the new object is larger.
        #
        # This makes target generation deterministic
        # instead of depending on annotation order.
        # ==================================================

        if (
            target[
                0,
                grid_y,
                grid_x
            ]
            > 0.5
        ):

            existing_area = (
                assigned_area[
                    grid_y,
                    grid_x
                ].item()
            )


            if (
                object_area
                <=
                existing_area
            ):

                continue


            # ----------------------------------------------
            # Clear old cell completely before replacing it.
            #
            # IMPORTANT:
            # This prevents the previous object's class
            # one-hot value from remaining in the cell.
            # ----------------------------------------------

            target[
                :,
                grid_y,
                grid_x
            ] = 0.0


        # ==================================================
        # POSITION RELATIVE TO GRID CELL
        # ==================================================

        cell_x = (
            center_x
            *
            grid_size
            -
            grid_x
        )

        cell_y = (
            center_y
            *
            grid_size
            -
            grid_y
        )


        # ==================================================
        # OBJECTNESS
        # ==================================================

        target[
            0,
            grid_y,
            grid_x
        ] = 1.0


        # ==================================================
        # BOUNDING BOX
        # ==================================================

        target[
            1,
            grid_y,
            grid_x
        ] = cell_x

        target[
            2,
            grid_y,
            grid_x
        ] = cell_y

        target[
            3,
            grid_y,
            grid_x
        ] = width

        target[
            4,
            grid_y,
            grid_x
        ] = height


        # ==================================================
        # CLASS
        # ==================================================

        target[
            5 + category,
            grid_y,
            grid_x
        ] = 1.0


        # ==================================================
        # REMEMBER AREA
        # ==================================================

        assigned_area[
            grid_y,
            grid_x
        ] = object_area


    return target


# ==================================================
# TEST
# ==================================================

if __name__ == "__main__":

    # --------------------------------------------------
    # Normal objects
    # --------------------------------------------------

    boxes = torch.tensor(
        [
            [0.8311, 0.4141, 0.1063, 0.2713],
            [0.3833, 0.1404, 0.0635, 0.0981],
            [0.7356, 0.7910, 0.2089, 0.2083],
            [0.3669, 0.1565, 0.0448, 0.0944]
        ],
        dtype=torch.float32
    )

    categories = torch.tensor(
        [
            6,
            7,
            11,
            11
        ],
        dtype=torch.long
    )


    target = create_target_grid(
        boxes,
        categories
    )


    print(
        "Target shape:"
    )

    print(
        target.shape
    )


    print(
        "\nNumber of input objects:",
        len(boxes)
    )


    print(
        "Number of occupied cells:",
        int(
            target[0]
            .sum()
            .item()
        )
    )


    # ==================================================
    # PRINT OCCUPIED CELLS
    # ==================================================

    print(
        "\nOccupied grid cells:"
    )


    positions = torch.nonzero(
        target[0]
    )


    for grid_y, grid_x in positions:

        grid_y = int(
            grid_y
        )

        grid_x = int(
            grid_x
        )


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


        class_id = torch.argmax(
            class_values
        ).item()


        print(
            f"\nCell ({grid_x}, {grid_y})"
            f"\n  Box: {bbox.tolist()}"
            f"\n  Class: {class_id}"
        )


    # ==================================================
    # VERIFY ONE-HOT CLASS TARGET
    # ==================================================

    for grid_y, grid_x in positions:

        class_sum = target[
            5:,
            grid_y,
            grid_x
        ].sum()

        assert torch.isclose(
            class_sum,
            torch.tensor(1.0)
        )


    print(
        "\n✅ Class one-hot test passed!"
    )


    # ==================================================
    # COLLISION TEST
    # ==================================================
    #
    # Both boxes intentionally have centres in
    # the SAME grid cell.
    #
    # Second object is larger and should replace
    # the first object.
    # ==================================================

    collision_boxes = torch.tensor(
    [
        # Small object
        # center = (0.105, 0.105)
        # grid cell = (2, 2)
        [
            0.100,
            0.100,
            0.010,
            0.010
        ],

        # Larger object
        # center = (0.105, 0.105)
        # grid cell = (2, 2)
        #
        # Same centre as first object,
        # therefore guaranteed collision.
        [
            0.090,
            0.090,
            0.030,
            0.030
        ]
    ],
    dtype=torch.float32
)


    collision_categories = torch.tensor(
        [
            7,
            4
        ],
        dtype=torch.long
    )


    collision_target = create_target_grid(
        collision_boxes,
        collision_categories
    )


    collision_positions = torch.nonzero(
        collision_target[0]
    )


    print(
        "\nCollision test:"
    )

    print(
        "Input objects:",
        len(collision_boxes)
    )

    print(
        "Occupied cells:",
        len(collision_positions)
    )


    # Must become one cell
    assert (
        len(collision_positions)
        ==
        1
    )


    grid_y = int(
        collision_positions[0][0]
    )

    grid_x = int(
        collision_positions[0][1]
    )


    class_values = collision_target[
        5:,
        grid_y,
        grid_x
    ]


    selected_class = torch.argmax(
        class_values
    ).item()


    print(
        "Selected class:",
        selected_class
    )


    print(
        "Expected class:",
        4
    )


    # Larger second object should win
    assert (
        selected_class
        ==
        4
    )


    # Exactly ONE class must be active
    assert torch.isclose(
        class_values.sum(),
        torch.tensor(1.0)
    )


    print(
        "\n✅ Collision handling test passed!"
    )


    print(
        "\n✅ V3 TARGET GENERATOR TEST PASSED!"
    )