import shutil
import re
import argparse
from pathlib import Path


def setup_directories(base_path: Path, dir_names: list[str]):
    """Creates or wipes target directories under the siril-ready path."""
    for name in dir_names:
        target_dir = base_path / name
        if target_dir.exists():
            print(f"Clearing: {target_dir}")
            for item in target_dir.iterdir():
                if item.is_dir():
                    shutil.rmtree(item)
                else:
                    item.unlink()
        else:
            target_dir.mkdir(parents=True)


def get_unique_path(destination: Path) -> Path:
    """Handles collisions by appending an incrementing counter."""
    if not destination.exists():
        return destination

    stem, suffix = destination.stem, destination.suffix
    counter = 1
    while True:
        new_path = destination.with_name(f"{stem}_{counter}{suffix}")
        if not new_path.exists():
            return new_path
        counter += 1


def reorganize_fits(root: Path, lights_src_name: str):
    # Define the destination root: root / siril-ready / <lights_dir>
    dest_root = root / "siril-ready" / lights_src_name

    target_dirs = ["lights", "darks", "flats", "bias"]
    cali_subdirs = ["darks", "flats", "bias"]

    print(f"Destination initialized at: {dest_root}")
    setup_directories(dest_root, target_dirs)

    # 1. Process Lights (Source: root / <lights_dir>)
    lights_src_path = root / lights_src_name
    lights_dest_path = dest_root / "lights"

    if lights_src_path.is_dir():
        for fits_file in lights_src_path.rglob("*.fits"):
            filename_lower = fits_file.name.lower()
            if filename_lower.startswith("failed") or filename_lower.startswith(
                "stacked"
            ):
                continue

            dest = get_unique_path(lights_dest_path / fits_file.name)
            print(f"Copying Light: {fits_file.name} -> {dest.relative_to(dest_root)}")
            shutil.copy2(fits_file, dest)
    else:
        print(f"Warning: Lights source '{lights_src_path}' not found.")

    # 2. Process Calibration Frames (Source: root / CALI_FRAME / ...)
    cali_root = root / "CALI_FRAME"
    cam_regex = re.compile(r"^cam_0.*$")

    if cali_root.is_dir():
        for sub in cali_subdirs:
            source_cat = cali_root / sub
            dest_cat = dest_root / sub

            if not source_cat.is_dir():
                continue

            for folder in source_cat.iterdir():
                if folder.is_dir() and cam_regex.match(folder.name):
                    for fits_file in folder.rglob("*.fits"):
                        dest = get_unique_path(dest_cat / fits_file.name)
                        print(
                            f"Copying Cali:  {fits_file.name} -> {dest.relative_to(dest_root)}"
                        )
                        shutil.copy2(fits_file, dest)
    else:
        print(f"Warning: 'CALI_FRAME' not found in {root}")

    print(f"\nReorganization complete. Results in: {dest_root}")


def main():
    parser = argparse.ArgumentParser(
        description="Reorganize FITS files into a siril-ready directory structure."
    )
    parser.add_argument("directory", help="The root/starting directory.")
    parser.add_argument(
        "lights_dir",
        help="Subdirectory name under 'directory' containing the session lights.",
    )

    args = parser.parse_args()
    root = Path(args.directory).resolve()

    if not root.is_dir():
        print(f"Error: {root} is not a valid directory.")
        return

    reorganize_fits(root, args.lights_dir)


if __name__ == "__main__":
    main()
