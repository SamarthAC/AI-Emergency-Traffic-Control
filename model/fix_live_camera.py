with open('ai_emergency_demo.py', 'r') as f:
    content = f.read()

# Fix _find_live_camera_image to return None instead of raising error
old_find = '''def _find_live_camera_image(live_camera_dir: Path, camera_id: str) -> Path:
    """Resolve exactly one watched frame for a logical traffic camera."""
    matches = [
        live_camera_dir / f"{camera_id}{suffix}"
        for suffix in LIVE_CAMERA_SUFFIXES
        if (live_camera_dir / f"{camera_id}{suffix}").exists()
    ]

    if not matches:
        expected = ", ".join(
            f"{camera_id}{suffix}" for suffix in LIVE_CAMERA_SUFFIXES
        )
        raise FileNotFoundError(
            f"Live camera frame missing for {camera_id} in {live_camera_dir}. "
            f"Expected one of: {expected}"
        )

    if len(matches) > 1:
        names = ", ".join(path.name for path in matches)
        raise RuntimeError(
            f"Multiple live frames found for {camera_id}: {names}. "
            "Keep exactly one .jpg/.jpeg/.png file for each camera ID."
        )

    return matches[0]'''

new_find = '''def _find_live_camera_image(live_camera_dir: Path, camera_id: str) -> Path | None:
    """Resolve exactly one watched frame for a logical traffic camera. Returns None if not found."""
    matches = [
        live_camera_dir / f"{camera_id}{suffix}"
        for suffix in LIVE_CAMERA_SUFFIXES
        if (live_camera_dir / f"{camera_id}{suffix}").exists()
    ]

    if not matches:
        return None

    if len(matches) > 1:
        names = ", ".join(path.name for path in matches)
        raise RuntimeError(
            f"Multiple live frames found for {camera_id}: {names}. "
            "Keep exactly one .jpg/.jpeg/.png file for each camera ID."
        )

    return matches[0]'''

content = content.replace(old_find, new_find)

# Fix build_live_camera_args to skip cameras without images
old_build = '''def build_live_camera_args(live_camera_dir: Path) -> list[tuple[str, str]]:
    """Build startup camera arguments from the watched live camera folder."""
    if not live_camera_dir.exists():
        raise FileNotFoundError(
            f"Live camera folder not found:\n{live_camera_dir}\n"
            "Create it and add one frame per traffic camera before starting."
        )

    camera_args = []
    for camera_id in LIVE_TRAFFIC_CAMERA_IDS:
        image = _find_live_camera_image(live_camera_dir, camera_id)
        camera_args.append((camera_id, str(image)))
    return camera_args'''

new_build = '''def build_live_camera_args(live_camera_dir: Path) -> list[tuple[str, str]]:
    """Build startup camera arguments from the watched live camera folder.
    Skips cameras that don't have image files in the live_inputs folder.
    """
    if not live_camera_dir.exists():
        raise FileNotFoundError(
            f"Live camera folder not found:\n{live_camera_dir}\n"
            "Create it and add one frame per traffic camera before starting."
        )

    camera_args = []
    for camera_id in LIVE_TRAFFIC_CAMERA_IDS:
        image = _find_live_camera_image(live_camera_dir, camera_id)
        if image is not None:
            camera_args.append((camera_id, str(image)))
        else:
            print(f"[WARNING] No live frame found for {camera_id}, skipping...")
    return camera_args'''

content = content.replace(old_build, new_build)

with open('ai_emergency_demo.py', 'w') as f:
    f.write(content)

print('Fixed live camera handling to skip missing cameras')