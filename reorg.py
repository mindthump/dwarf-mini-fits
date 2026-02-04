import shutil
import re
import argparse
from pathlib import Path


def setup_directories(base_path: Path, dir_names: list[str]):
    """Creates or wipes target directories under the destination path."""
    for name in dir_names:
        target_dir = base_path / name
        if target_dir.exists():
            print(f"Cleaning existing target: {target_dir.name}")
            for item in target_dir.iterdir():
                if item.is_dir():
                    shutil.rmtree(item)
                else:
                    item.unlink()
        else:
            target_dir.mkdir(parents=True)


def get_unique_path(destination: Path) -> Path:
    """Appends _n to filename if a collision occurs."""
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
    # FIX: Use .name to ensure we get a relative string for the folder
    # even if the user provides an absolute path as an argument.
    session_subdir = Path(lights_src_name).name
    dest_root = root / "siril-ready" / session_subdir

    # Target plural names for Siril
    target_dirs = ["lights", "darks", "flats", "bias"]

    # Mapping: Source Folder Name -> Destination Folder Name
    cali_map = {"dark": "darks", "flat": "flats", "bias": "bias"}

    print(f"Organizing session into: {dest_root}")
    setup_directories(dest_root, target_dirs)

    # 1. Process Lights (Source: root / <lights_dir>)
    # We use the original lights_src_name here to find the source
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
            print(f"Copying Light: {fits_file.name} -> lights/{dest.name}")
            shutil.copy2(fits_file, dest)
    else:
        print(f"Warning: Lights source '{lights_src_path}' not found.")

    # 2. Process Calibration Frames
    cali_root = root / "CALI_FRAME"
    cam_regex = re.compile(r"^cam_0.*$")

    if cali_root.is_dir():
        for src_sub, dest_sub in cali_map.items():
            source_cat = cali_root / src_sub
            dest_cat = dest_root / dest_sub

            if not source_cat.is_dir():
                continue

            for folder in source_cat.iterdir():
                if folder.is_dir() and cam_regex.match(folder.name):
                    for fits_file in folder.rglob("*.fits"):
                        dest = get_unique_path(dest_cat / fits_file.name)
                        print(
                            f"Copying Cali:  {fits_file.name} -> {dest_sub}/{dest.name}"
                        )
                        shutil.copy2(fits_file, dest)
    else:
        print(f"Warning: 'CALI_FRAME' not found in {root}")

    print(f"\nSuccess! Files staged for Siril in: {dest_root}")


def main():
    parser = argparse.ArgumentParser(
        description="Stage Dwarf telescope FITS files for Siril."
    )
    parser.add_argument("directory", help="The root session directory.")
    parser.add_argument(
        "lights_dir",
        help="Subdirectory name (under directory) containing the raw lights.",
    )

    args = parser.parse_args()
    root = Path(args.directory).resolve()

    if not root.is_dir():
        print(f"Error: {root} is not a valid directory.")
        return

    # Check if lights_dir exists before we start
    if not (root / args.lights_dir).is_dir():
        print(
            f"Error: Source lights directory '{args.lights_dir}' not found under {root}."
        )
        return

    reorganize_fits(root, args.lights_dir)


if __name__ == "__main__":
    main()
