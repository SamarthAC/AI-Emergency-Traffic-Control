import torch
import torch.nn as nn


class TrafficCNN(nn.Module):

    def __init__(self, num_classes=14):

        super(TrafficCNN, self).__init__()

        # -----------------------------
        # CNN FEATURE EXTRACTOR
        # -----------------------------
        self.features = nn.Sequential(

            nn.Conv2d(
                in_channels=3,
                out_channels=32,
                kernel_size=3,
                padding=1
            ),
            nn.ReLU(),
            nn.MaxPool2d(2),

            nn.Conv2d(
                in_channels=32,
                out_channels=64,
                kernel_size=3,
                padding=1
            ),
            nn.ReLU(),
            nn.MaxPool2d(2),

            nn.Conv2d(
                in_channels=64,
                out_channels=128,
                kernel_size=3,
                padding=1
            ),
            nn.ReLU(),
            nn.MaxPool2d(2)
        )

        # -----------------------------
        # DETECTION HEAD
        # -----------------------------
        # Each grid cell predicts:
        #
        # 1 object confidence
        # 4 bounding-box values
        # num_classes class scores
        #
        # Total = 5 + num_classes

        self.detection_head = nn.Conv2d(
            in_channels=128,
            out_channels=5 + num_classes,
            kernel_size=1
        )

    def forward(self, x):

        # Extract visual features
        x = self.features(x)

        # Make predictions
        x = self.detection_head(x)

        return x


# ------------------------------------------------
# TEST THE MODEL
# ------------------------------------------------

if __name__ == "__main__":

    model = TrafficCNN(num_classes=14)

    # One test image
    test_image = torch.randn(1, 3, 224, 224)

    output = model(test_image)

    print("Input shape:")
    print(test_image.shape)

    print("\nOutput shape:")
    print(output.shape)

    print("\nModel:")
    print(model)