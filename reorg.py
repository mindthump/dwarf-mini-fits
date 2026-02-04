import shutil
import re
import argparse
from pathlib import Path
from astropy.io import fits


def get_fits_metadata(file_path: Path):
    """Extracts essential metadata for validation."""
    try:
        with fits.open(file_path) as hdul:
            header = hdul[0].header
            return {
                "exposure": header.get("EXPOSURE") or header.get("EXPTIME"),
                "gain": header.get("GAIN") or header.get("ISO"),
                "x": header.get("NAXIS1"),
                "y": header.get("NAXIS2"),
            }
    except Exception as e:
        print(f"Error reading {file_path.name}: {e}")
        return None


def setup_directories(base_path: Path, dir_names: list[str]):
    """Creates or wipes target directories."""
    for name in dir_names:
        target_dir = base_path / name
        if target_dir.exists():
            print(f"Cleaning: {target_dir.name}")
            for item in target_dir.iterdir():
                if item.is_dir():
                    shutil.rmtree(item)
                else:
                    item.unlink()
        else:
            target_dir.mkdir(parents=True)


def get_unique_path(destination: Path) -> Path:
    """Standard stem_n.suffix collision handling."""
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
    session_subdir = Path(lights_src_name).name
    dest_root = root / "siril-ready" / session_subdir
    target_dirs = ["lights", "darks", "flats", "biases"]
    cali_map = {"dark": "darks", "flat": "flats", "bias": "biases"}

    setup_directories(dest_root, target_dirs)

    # 1. Process Lights & Establish Baseline Metadata
    lights_src_path = root / lights_src_name
    lights_dest_path = dest_root / "lights"
    baseline = None

    if lights_src_path.is_dir():
        for fits_file in lights_src_path.rglob("*.fits"):
            if any(fits_file.name.lower().startswith(s) for s in ["failed", "stacked"]):
                continue

            if baseline is None:
                baseline = get_fits_metadata(fits_file)

            dest = get_unique_path(lights_dest_path / fits_file.name)
            shutil.copy2(fits_file, dest)

    if not baseline:
        print("Error: No valid light frames found to establish baseline.")
        return

    print(
        f"Baseline (Lights): {baseline['x']}x{baseline['y']}, Gain: {baseline['gain']}"
    )

    # 2. Process Calibration Frames with Verification
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
                        meta = get_fits_metadata(fits_file)
                        if not meta:
                            continue

                        # Validation Logic
                        # Flats and Darks should match dimensions; Darks usually match exposure
                        if meta["x"] != baseline["x"] or meta["y"] != baseline["y"]:
                            continue

                        if (
                            dest_sub == "darks"
                            and meta["exposure"] != baseline["exposure"]
                        ):
                            # Optional: Dwarf darks often match exposure exactly
                            continue

                        dest = get_unique_path(dest_cat / fits_file.name)
                        shutil.copy2(fits_file, dest)

    print(f"\nSuccess! Verified files staged in: {dest_root}")


def main():
    parser = argparse.ArgumentParser(
        description="Stage verified Dwarf FITS files for Siril."
    )
    parser.add_argument("directory", help="The root session directory.")
    parser.add_argument("lights_dir", help="Subdirectory name containing raw lights.")
    args = parser.parse_args()
    root = Path(args.directory).resolve()

    if root.is_dir() and (root / args.lights_dir).is_dir():
        reorganize_fits(root, args.lights_dir)
    else:
        print("Invalid directory paths provided.")


if __name__ == "__main__":
    main()
