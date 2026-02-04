import shutil
import re
import argparse
from pathlib import Path


def setup_directories(base_path: Path, dir_names: list[str]):
    """Creates or clears target directories. Robust to existing non-empty dirs."""
    for name in dir_names:
        target_dir = base_path / name
        if target_dir.exists():
            for item in target_dir.iterdir():
                if item.is_dir():
                    shutil.rmtree(item)
                else:
                    item.unlink()
        else:
            target_dir.mkdir(parents=True)


def get_unique_path(destination: Path) -> Path:
    """Standard collision handling: stem_n.suffix."""
    if not destination.exists():
        return destination

    stem, suffix = destination.stem, destination.suffix
    counter = 1
    while True:
        new_path = destination.with_name(f"{stem}_{counter}{suffix}")
        if not new_path.exists():
            return new_path
        counter += 1


def reorganize_fits(root_path: Path, lights_src_name: str, use_move: bool):
    target_dirs = ["lights", "darks", "flats", "bias"]
    cali_subdirs = ["darks", "flats", "bias"]

    setup_directories(root_path, target_dirs)

    # Define the transfer operation
    op_name = "Moving" if use_move else "Copying"
    transfer_func = shutil.move if use_move else shutil.copy2

    # 1. Process Lights
    lights_src_path = root_path / lights_src_name
    if lights_src_path.is_dir():
        for fits_file in lights_src_path.rglob("*.fits"):
            if fits_file.name.startswith("failed"):
                continue

            dest = get_unique_path(root_path / "lights" / fits_file.name)
            print(
                f"{op_name} Light: {fits_file.relative_to(root_path)} -> {dest.relative_to(root_path)}"
            )
            transfer_func(fits_file, dest)

    # 2. Process Calibration Frames
    cali_root = root_path / "CALI_FRAME"
    cam_regex = re.compile(r"^cam_0.*$")

    if cali_root.is_dir():
        for sub in cali_subdirs:
            source_cat = cali_root / sub
            if not source_cat.is_dir():
                continue

            for folder in source_cat.iterdir():
                if folder.is_dir() and cam_regex.match(folder.name):
                    for fits_file in folder.rglob("*.fits"):
                        dest = get_unique_path(root_path / sub / fits_file.name)
                        print(
                            f"{op_name} Cali:  {fits_file.relative_to(root_path)} -> {dest.relative_to(root_path)}"
                        )
                        transfer_func(fits_file, dest)


def main():
    parser = argparse.ArgumentParser(
        description="Reorganize FITS files with optional move support."
    )
    parser.add_argument("directory", help="The starting root directory.")
    parser.add_argument(
        "lights_dir", help="Subdirectory name under 'directory' containing lights."
    )
    parser.add_argument(
        "--move", action="store_true", help="Move files instead of copying them."
    )

    args = parser.parse_args()
    root = Path(args.directory).resolve()

    if not root.is_dir():
        print(f"Error: {root} is not a directory.")
        return

    reorganize_fits(root, args.lights_dir, args.move)


if __name__ == "__main__":
    main()
