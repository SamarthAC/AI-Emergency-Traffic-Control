import torch
import torch.nn as nn
import torch.nn.functional as F


# ==========================================================
# SETTINGS
# ==========================================================

# BMD classes 0-13
# Ambulance class 14
NUM_CLASSES = 15

IMAGE_SIZE = 448

SMALL_GRID_SIZE = 56
LARGE_GRID_SIZE = 28


# ==========================================================
# CONVOLUTION BLOCK
# ==========================================================

class ConvBNAct(nn.Module):

    def __init__(
        self,
        in_channels,
        out_channels,
        kernel_size=3,
        stride=1,
        padding=1
    ):

        super().__init__()

        self.block = nn.Sequential(

            nn.Conv2d(
                in_channels,
                out_channels,
                kernel_size=kernel_size,
                stride=stride,
                padding=padding,
                bias=False
            ),

            nn.BatchNorm2d(
                out_channels
            ),

            nn.SiLU(
                inplace=True
            )
        )

    def forward(
        self,
        x
    ):

        return self.block(
            x
        )


# ==========================================================
# RESIDUAL BLOCK
# ==========================================================

class ResidualBlock(nn.Module):

    def __init__(
        self,
        channels
    ):

        super().__init__()

        hidden_channels = (
            channels // 2
        )

        self.conv1 = ConvBNAct(
            channels,
            hidden_channels,
            kernel_size=1,
            padding=0
        )

        self.conv2 = ConvBNAct(
            hidden_channels,
            channels,
            kernel_size=3,
            padding=1
        )

    def forward(
        self,
        x
    ):

        residual = x

        x = self.conv1(
            x
        )

        x = self.conv2(
            x
        )

        return (
            x + residual
        )


# ==========================================================
# RESIDUAL STAGE
# ==========================================================

class ResidualStage(nn.Module):

    def __init__(
        self,
        in_channels,
        out_channels,
        num_blocks
    ):

        super().__init__()

        # Downsample by factor 2
        self.downsample = ConvBNAct(
            in_channels,
            out_channels,
            kernel_size=3,
            stride=2,
            padding=1
        )

        blocks = []

        for _ in range(
            num_blocks
        ):

            blocks.append(
                ResidualBlock(
                    out_channels
                )
            )

        self.blocks = nn.Sequential(
            *blocks
        )

    def forward(
        self,
        x
    ):

        x = self.downsample(
            x
        )

        x = self.blocks(
            x
        )

        return x


# ==========================================================
# DETECTION HEAD
# ==========================================================

class DetectionHead(nn.Module):

    def __init__(
        self,
        in_channels,
        num_classes
    ):

        super().__init__()

        # 1 objectness
        # 4 bbox
        # num_classes class logits
        output_channels = (
            5 + num_classes
        )

        self.head = nn.Sequential(

            ConvBNAct(
                in_channels,
                in_channels,
                kernel_size=3,
                padding=1
            ),

            nn.Conv2d(
                in_channels,
                output_channels,
                kernel_size=1
            )
        )

    def forward(
        self,
        x
    ):

        return self.head(
            x
        )


# ==========================================================
# V4 TRAFFIC DETECTOR
# ==========================================================

class TrafficDetectorV4(nn.Module):

    def __init__(
        self,
        num_classes=NUM_CLASSES
    ):

        super().__init__()

        self.num_classes = (
            num_classes
        )

        # ==================================================
        # STEM
        #
        # 448 -> 448
        # ==================================================

        self.stem = ConvBNAct(
            3,
            32,
            kernel_size=3,
            stride=1,
            padding=1
        )

        # ==================================================
        # BACKBONE
        # ==================================================

        # 448 -> 224
        self.stage1 = ResidualStage(
            32,
            64,
            num_blocks=1
        )

        # 224 -> 112
        self.stage2 = ResidualStage(
            64,
            128,
            num_blocks=2
        )

        # 112 -> 56
        self.stage3 = ResidualStage(
            128,
            256,
            num_blocks=3
        )

        # 56 -> 28
        self.stage4 = ResidualStage(
            256,
            512,
            num_blocks=3
        )

        # ==================================================
        # DEEP FEATURE PROCESSING
        # ==================================================

        self.deep_processing = nn.Sequential(

            ConvBNAct(
                512,
                256,
                kernel_size=1,
                padding=0
            ),

            ConvBNAct(
                256,
                512,
                kernel_size=3,
                padding=1
            ),

            ConvBNAct(
                512,
                256,
                kernel_size=1,
                padding=0
            )
        )

        # ==================================================
        # LARGE OBJECT FEATURE
        #
        # 28x28
        # ==================================================

        self.large_feature = ConvBNAct(
            256,
            256,
            kernel_size=3,
            padding=1
        )

        # ==================================================
        # DEEP FEATURE REDUCTION FOR SMALL HEAD
        #
        # 28x28 -> upsample later to 56x56
        # ==================================================

        self.reduce_deep = ConvBNAct(
            256,
            128,
            kernel_size=1,
            padding=0
        )

        # ==================================================
        # STAGE-3 FEATURE REDUCTION
        #
        # 56x56
        # ==================================================

        self.reduce_stage3 = ConvBNAct(
            256,
            128,
            kernel_size=1,
            padding=0
        )

        # ==================================================
        # SMALL FEATURE FUSION
        #
        # 128 deep
        # +
        # 128 stage3
        # =
        # 256
        # ==================================================

        self.small_fusion = nn.Sequential(

            ConvBNAct(
                256,
                256,
                kernel_size=3,
                padding=1
            ),

            ConvBNAct(
                256,
                256,
                kernel_size=3,
                padding=1
            )
        )

        # ==================================================
        # DETECTION HEADS
        # ==================================================

        self.small_head = DetectionHead(
            256,
            num_classes
        )

        self.large_head = DetectionHead(
            256,
            num_classes
        )

    # ======================================================
    # FORWARD
    # ======================================================

    def forward(
        self,
        x
    ):

        # ==================================================
        # BACKBONE
        # ==================================================

        x = self.stem(
            x
        )

        # 224x224
        x = self.stage1(
            x
        )

        # 112x112
        x = self.stage2(
            x
        )

        # 56x56
        feature_56 = self.stage3(
            x
        )

        # 28x28
        feature_28 = self.stage4(
            feature_56
        )

        # ==================================================
        # DEEP FEATURES
        # ==================================================

        deep = self.deep_processing(
            feature_28
        )

        # ==================================================
        # LARGE HEAD
        #
        # 28x28
        # ==================================================

        large_feature = (
            self.large_feature(
                deep
            )
        )

        large_output = (
            self.large_head(
                large_feature
            )
        )

        # ==================================================
        # SMALL HEAD
        #
        # 56x56
        # ==================================================

        deep_reduced = (
            self.reduce_deep(
                deep
            )
        )

        deep_upsampled = (
            F.interpolate(
                deep_reduced,
                size=feature_56.shape[-2:],
                mode="nearest"
            )
        )

        stage3_reduced = (
            self.reduce_stage3(
                feature_56
            )
        )

        # Feature fusion
        fused = torch.cat(
            [
                deep_upsampled,
                stage3_reduced
            ],
            dim=1
        )

        fused = self.small_fusion(
            fused
        )

        small_output = (
            self.small_head(
                fused
            )
        )

        # ==================================================
        # RETURN
        # ==================================================

        return {
            "small":
                small_output,

            "large":
                large_output
        }


# ==========================================================
# MODEL TEST
# ==========================================================

if __name__ == "__main__":

    print(
        "=" * 70
    )

    print(
        "V4 15-CLASS MULTI-SCALE MODEL TEST"
    )

    print(
        "=" * 70
    )

    # ======================================================
    # DEVICE
    # ======================================================

    device = torch.device(
        "cuda"
        if torch.cuda.is_available()
        else "cpu"
    )

    print(
        "Device:",
        device
    )

    # ======================================================
    # MODEL
    # ======================================================

    model = TrafficDetectorV4(
        num_classes=NUM_CLASSES
    ).to(
        device
    )

    print(
        "Number of classes:",
        model.num_classes
    )

    print(
        "Expected output channels:",
        5 + model.num_classes
    )

    # ======================================================
    # FAKE INPUT
    # ======================================================

    x = torch.randn(
        1,
        3,
        IMAGE_SIZE,
        IMAGE_SIZE,
        device=device
    )

    model.eval()

    with torch.no_grad():

        outputs = model(
            x
        )

    small_output = (
        outputs[
            "small"
        ]
    )

    large_output = (
        outputs[
            "large"
        ]
    )

    # ======================================================
    # DISPLAY SHAPES
    # ======================================================

    print(
        "\nInput:",
        x.shape
    )

    print(
        "Small output:",
        small_output.shape
    )

    print(
        "Large output:",
        large_output.shape
    )

    # ======================================================
    # PARAMETER COUNT
    # ======================================================

    total_parameters = sum(
        parameter.numel()
        for parameter
        in model.parameters()
    )

    trainable_parameters = sum(
        parameter.numel()
        for parameter
        in model.parameters()
        if parameter.requires_grad
    )

    print(
        "\nTotal parameters:",
        f"{total_parameters:,}"
    )

    print(
        "Trainable parameters:",
        f"{trainable_parameters:,}"
    )

    # ======================================================
    # EXPECTED SHAPES
    # ======================================================

    expected_channels = (
        5 + NUM_CLASSES
    )

    expected_small = (
        1,
        expected_channels,
        SMALL_GRID_SIZE,
        SMALL_GRID_SIZE
    )

    expected_large = (
        1,
        expected_channels,
        LARGE_GRID_SIZE,
        LARGE_GRID_SIZE
    )

    # ======================================================
    # VALIDATION
    # ======================================================

    small_ok = (
        tuple(
            small_output.shape
        )
        ==
        expected_small
    )

    large_ok = (
        tuple(
            large_output.shape
        )
        ==
        expected_large
    )

    finite_ok = (
        torch.isfinite(
            small_output
        ).all()
        and
        torch.isfinite(
            large_output
        ).all()
    )

    class_ok = (
        model.num_classes
        == 15
    )

    channel_ok = (
        small_output.shape[1]
        == 20
        and
        large_output.shape[1]
        == 20
    )

    # ======================================================
    # PRINT TESTS
    # ======================================================

    print(
        "\nNumber of classes:",
        "PASS"
        if class_ok
        else "FAIL"
    )

    print(
        "20-channel heads:",
        "PASS"
        if channel_ok
        else "FAIL"
    )

    print(
        "Small head shape:",
        "PASS"
        if small_ok
        else "FAIL"
    )

    print(
        "Large head shape:",
        "PASS"
        if large_ok
        else "FAIL"
    )

    print(
        "Finite output:",
        "PASS"
        if finite_ok
        else "FAIL"
    )

    # ======================================================
    # FINAL RESULT
    # ======================================================

    if (
        class_ok
        and
        channel_ok
        and
        small_ok
        and
        large_ok
        and
        finite_ok
    ):

        print(
            "\n"
            "✅ V4 15-CLASS MODEL "
            "FORWARD TEST PASSED!"
        )

    else:

        print(
            "\n"
            "❌ V4 15-CLASS MODEL "
            "TEST FAILED!"
        )

    print(
        "=" * 70
    )