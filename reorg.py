import shutil
import re
from pathlib import Path


def setup_directories(base_path, dir_names):
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


def get_unique_path(destination):
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


def reorganize_fits():
    cwd = Path.cwd()
    target_dirs = ["lights", "darks", "flats", "bias"]
    cali_subdirs = ["darks", "flats", "bias"]

    setup_directories(cwd, target_dirs)

    cali_frame_root = cwd / "CALI_FRAME"
    if not cali_frame_root.exists():
        print(f"Aborting: Source directory '{cali_frame_root}' not found.")
        return

    cam_regex = re.compile(r"^cam_0.*$")

    for sub in cali_subdirs:
        source_category_path = cali_frame_root / sub
        dest_category_path = cwd / sub

        if not source_category_path.exists():
            continue

        # Iterate through subdirectories matching 'cam_0*'
        for folder in source_category_path.iterdir():
            if folder.is_dir() and cam_regex.match(folder.name):
                for fits_file in folder.rglob("*.fits"):
                    dest_file_path = dest_category_path / fits_file.name
                    final_destination = get_unique_path(dest_file_path)

                    # Informational print before copy
                    print(
                        f"Copying: {fits_file.relative_to(cwd)} -> {final_destination.relative_to(cwd)}"
                    )

                    try:
                        shutil.copy2(fits_file, final_destination)
                    except Exception as e:
                        print(f"Failed to copy {fits_file.name}: {e}")

    print("\nReorganization complete.")


if __name__ == "__main__":
    reorganize_fits()
