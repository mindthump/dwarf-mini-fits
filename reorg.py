import shutil
import re
import argparse
from pathlib import Path


def setup_directories(base_path: Path, dir_names: list[str]):
    """Creates or clears the target directories."""
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
    """Increments filename if a collision exists."""
    if not destination.exists():
        return destination

    stem = destination.stem
    suffix = destination.suffix
    counter = 1
    while True:
        new_path = destination.with_name(f"{stem}_{counter}{suffix}")
        if not new_path.exists():
            return new_path
        counter += 1


def reorganize_fits(root_path: Path):
    target_dirs = ["lights", "darks", "flats", "bias"]
    cali_subdirs = ["darks", "flats", "bias"]

    # 1. Initialize top-level directories
    print(f"Initializing target directories in: {root_path}")
    setup_directories(root_path, target_dirs)

    cali_frame_root = root_path / "CALI_FRAME"
    if not cali_frame_root.exists():
        print(f"Aborting: Source directory '{cali_frame_root}' not found.")
        return

    cam_regex = re.compile(r"^cam_0.*$")

    # 2. Process CALI_FRAME subdirectories
    for sub in cali_subdirs:
        source_category_path = cali_frame_root / sub
        dest_category_path = root_path / sub

        if not source_category_path.exists():
            continue

        for folder in source_category_path.iterdir():
            if folder.is_dir() and cam_regex.match(folder.name):
                for fits_file in folder.rglob("*.fits"):
                    dest_file_path = dest_category_path / fits_file.name
                    final_destination = get_unique_path(dest_file_path)

                    # Print relative to the provided root for cleaner logs
                    try:
                        print(
                            f"Copying: {fits_file.relative_to(root_path)} -> {final_destination.relative_to(root_path)}"
                        )
                        shutil.copy2(fits_file, final_destination)
                    except Exception as e:
                        print(f"Error copying {fits_file}: {e}")

    print("\nReorganization complete.")


def main():
    parser = argparse.ArgumentParser(
        description="Reorganize FITS files from CALI_FRAME subdirs."
    )
    parser.add_argument(
        "directory",
        nargs="?",
        default=".",
        help="The root directory to process (default: current directory)",
    )

    args = parser.parse_args()
    root_path = Path(args.directory).resolve()

    if not root_path.is_dir():
        print(f"Error: '{root_path}' is not a valid directory.")
        return

    reorganize_fits(root_path)


if __name__ == "__main__":
    main()
