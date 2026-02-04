import shutil
import re
from pathlib import Path


def setup_directories(base_path, dir_names):
    """Creates or clears the target directories."""
    for name in dir_names:
        target_dir = base_path / name
        if target_dir.exists():
            # Delete contents but keep the directory
            for item in target_dir.iterdir():
                if item.is_dir():
                    shutil.rmtree(item)
                else:
                    item.unlink()
        else:
            target_dir.mkdir(parents=True)


def get_unique_path(destination):
    """Increments filename if a collision exists (e.g., image.fits -> image_1.fits)."""
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


def reorganize_fits():
    cwd = Path.cwd()
    target_dirs = ["lights", "darks", "flats", "bias"]
    cali_subdirs = ["darks", "flats", "bias"]

    # 1. Initialize top-level directories
    print("Initializing directories...")
    setup_directories(cwd, target_dirs)

    cali_frame_root = cwd / "CALI_FRAME"
    if not cali_frame_root.exists():
        print(f"Error: {cali_frame_root} not found.")
        return

    # Regex for subdirectories starting with cam_0
    cam_regex = re.compile(r"^cam_0.*$")

    # 2. Process CALI_FRAME subdirectories
    for sub in cali_subdirs:
        source_category_path = cali_frame_root / sub
        dest_category_path = cwd / sub

        if not source_category_path.exists():
            continue

        print(f"Processing category: {sub}...")

        # Find subdirectories matching the regex
        for folder in source_category_path.iterdir():
            if folder.is_dir() and cam_regex.match(folder.name):
                # Find all .fits files (recursively or just direct children)
                for fits_file in folder.rglob("*.fits"):
                    dest_file_path = dest_category_path / fits_file.name

                    # Handle duplicate names
                    final_destination = get_unique_path(dest_file_path)

                    shutil.copy2(fits_file, final_destination)

    print("Reorganization complete.")


if __name__ == "__main__":
    reorganize_fits()
