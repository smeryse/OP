from pathlib import Path


def load_images(directory: str):
    return sorted(Path(directory).glob("*.png"))
