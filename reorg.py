import shutil
import re
import argparse
from pathlib import Path


def setup_directories(base_path: Path, dir_names: list[str]):
    """Idempotent setup: creates dirs or wipes contents inside the session directory."""
    for name in dir_names:
        target_dir = base_path / name
        if target_dir.exists():
            print(f"Clearing existing directory: {target_dir.name}")
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


def reorganize_fits(session_path: Path, lights_src_name: str, use_move: bool):
    # These will now be created inside session_path
    target_dirs = ["lights", "darks", "flats", "bias"]
    cali_subdirs = ["darks", "flats", "bias"]

    # 1. Initialize target directories INSIDE the session directory
    setup_directories(session_path, target_dirs)

    transfer_func = shutil.move if use_move else shutil.copy2
    op_label = "Moving" if use_move else "Copying"

    # 2. Process Lights (source is session_path/lights_src_name)
    lights_src_path = session_path / lights_src_name
    lights_dest_path = session_path / "lights"

    if (
        lights_src_path.is_dir()
        and lights_src_path.resolve() != lights_dest_path.resolve()
    ):
        for fits_file in lights_src_path.rglob("*.fits"):
            filename_lower = fits_file.name.lower()
            if filename_lower.startswith("failed") or filename_lower.startswith(
                "stacked"
            ):
                continue

            dest = get_unique_path(lights_dest_path / fits_file.name)
            print(f"{op_label} Light: {fits_file.name} -> lights/{dest.name}")
            transfer_func(fits_file, dest)
    else:
        if not lights_src_path.is_dir():
            print(f"Warning: Lights source '{lights_src_path}' not found.")

    # 3. Process Calibration Frames (source is session_path/CALI_FRAME/...)
    cali_root = session_path / "CALI_FRAME"
    cam_regex = re.compile(r"^cam_0.*$")

    if cali_root.is_dir():
        for sub in cali_subdirs:
            source_cat = cali_root / sub
            dest_cat = session_path / sub

            if not source_cat.is_dir():
                continue

            for folder in source_cat.iterdir():
                if folder.is_dir() and cam_regex.match(folder.name):
                    for fits_file in folder.rglob("*.fits"):
                        dest = get_unique_path(dest_cat / fits_file.name)
                        print(
                            f"{op_label} Cali:  {fits_file.name} -> {sub}/{dest.name}"
                        )
                        transfer_func(fits_file, dest)
    else:
        print(f"Warning: 'CALI_FRAME' not found in {session_path}")

    print(f"\nReorganization of {session_path.name} complete.")


def main():
    parser = argparse.ArgumentParser(
        description="Reorganize FITS files within a specific session directory."
    )
    parser.add_argument(
        "directory", help="The session-specific directory (e.g., /data/2024-02-03)."
    )
    parser.add_argument(
        "lights_dir", help="Subdirectory name inside 'directory' containing raw lights."
    )
    parser.add_argument(
        "--move", action="store_true", help="Move files instead of copying."
    )

    args = parser.parse_args()
    session_path = Path(args.directory).resolve()

    if not session_path.is_dir():
        print(f"Error: {session_path} is not a valid directory.")
        return

    reorganize_fits(session_path, args.lights_dir, args.move)


if __name__ == "__main__":
    main()
