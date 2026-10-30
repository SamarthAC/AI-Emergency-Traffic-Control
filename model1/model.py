import torch
import torch.nn as nn


class TrafficCNN(nn.Module):

    def __init__(self, num_classes=14):

        super().__init__()

        self.features = nn.Sequential(

            # ==================================
            # BLOCK 1
            # 448 → 224
            # ==================================

            nn.Conv2d(
                3,
                32,
                kernel_size=3,
                padding=1
            ),

            nn.BatchNorm2d(32),
            nn.ReLU(),

            nn.Conv2d(
                32,
                32,
                kernel_size=3,
                padding=1
            ),

            nn.BatchNorm2d(32),
            nn.ReLU(),

            nn.MaxPool2d(2),


            # ==================================
            # BLOCK 2
            # 224 → 112
            # ==================================

            nn.Conv2d(
                32,
                64,
                kernel_size=3,
                padding=1
            ),

            nn.BatchNorm2d(64),
            nn.ReLU(),

            nn.Conv2d(
                64,
                64,
                kernel_size=3,
                padding=1
            ),

            nn.BatchNorm2d(64),
            nn.ReLU(),

            nn.MaxPool2d(2),


            # ==================================
            # BLOCK 3
            # 112 → 56
            # ==================================

            nn.Conv2d(
                64,
                128,
                kernel_size=3,
                padding=1
            ),

            nn.BatchNorm2d(128),
            nn.ReLU(),

            nn.Conv2d(
                128,
                128,
                kernel_size=3,
                padding=1
            ),

            nn.BatchNorm2d(128),
            nn.ReLU(),

            nn.MaxPool2d(2),


            # ==================================
            # BLOCK 4
            # 56 → 28
            # ==================================

            nn.Conv2d(
                128,
                256,
                kernel_size=3,
                padding=1
            ),

            nn.BatchNorm2d(256),
            nn.ReLU(),

            nn.Conv2d(
                256,
                256,
                kernel_size=3,
                padding=1
            ),

            nn.BatchNorm2d(256),
            nn.ReLU(),

            nn.MaxPool2d(2),

        )


        # ==================================
        # DETECTION HEAD
        # ==================================

        self.detection_head = nn.Sequential(

            nn.Conv2d(
                256,
                256,
                kernel_size=3,
                padding=1
            ),

            nn.BatchNorm2d(256),
            nn.ReLU(),

            nn.Conv2d(
                256,
                5 + num_classes,
                kernel_size=1
            )
        )


    def forward(self, x):

        x = self.features(x)

        x = self.detection_head(x)

        return x


# ==================================
# TEST
# ==================================

if __name__ == "__main__":

    model = TrafficCNN(
        num_classes=14
    )

    dummy_input = torch.randn(
        1,
        3,
        448,
        448
    )

    output = model(
        dummy_input
    )

    print(
        "Input:",
        dummy_input.shape
    )

    print(
        "Output:",
        output.shape
    )