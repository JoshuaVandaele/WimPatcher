import argparse
import os
import sys
import tempfile

from modules.iso import create_iso_from_folder, extract_iso, mount_iso, unmount_iso
from modules.usb import prepare_usb_drive
from modules.utils import Operations, read_toml, run_as_admin
from modules.wim import (
    delete_other_editions,
    list_wim_indexes,
    mount_wim,
    optimize_wim_file,
    optimize_wim_image,
    unmount_wim,
)


def create_custom_iso(iso_file: str, output_path: str):
    with tempfile.TemporaryDirectory() as tmpdir:
        extract_iso(iso_file, tmpdir)

        patch_wim(f"{tmpdir}\\sources\\install.wim")

        print("Repacking...")
        create_iso_from_folder(tmpdir, output_path)

        print("Cleaning up...")


def create_bootable_usb(iso_file: str, drive_letter: str):
    drive_path = f"{drive_letter}:"
    prepare_usb_drive(iso_file, drive_path)

    patch_wim(f"{drive_path}\\sources\\install.wim")


def display_wim_editions(wim_info: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    """
    Displays a list of available Windows Imaging Format (WIM) file editions and returns a dictionary of valid indexes.

    Args:
        wim_info (List[Dict[str, str]]): A list of dictionaries containing information about the WIM file indexes.

    Returns:
        A dictionary containing the valid indexes and their associated information.
    """
    valid_indexes = {}
    for info in wim_info:
        index = info["Index"]
        valid_indexes[info["Name"]] = info
        print(f"{index} - {info['Name']} ({info['Size']})")
    return valid_indexes


def patch_wim(wim_file: str):
    wim_info = list_wim_indexes(wim_file)

    if len(wim_info) >= 1:
        select_edition(wim_info, wim_file)

    print("Mounting WIM file...")
    wim_mount_path = mount_wim(wim_file)
    try:
        # Do stuff in wim_mount_path here
        with open(wim_mount_path + "\\test.txt", "w") as file:
            file.write("this should appear in the wim file")

        print("Optimizing WIM image...")
        optimize_wim_image(wim_mount_path)
    finally:
        print("Unmounting WIM file...")
        unmount_wim(wim_mount_path)

    print("Optimizing WIM file...")
    optimize_wim_file(wim_file)


def select_edition(wim_info: list[dict[str, str]], wim_file: str):
    global CONFIG
    selected_edition = CONFIG["general"]["Edition"]
    print("Available editions:")
    valid_indexes = display_wim_editions(wim_info)

    print(f"Selecting edition: {selected_edition}")
    if selected_edition in valid_indexes:
        selection = valid_indexes[selected_edition]
    else:
        raise ValueError(f"'{selected_edition}' is not a valid selection!")

    delete_other_editions(wim_file, selection)


def main():
    run_as_admin()
    parser = argparse.ArgumentParser(
        description="WimPatcher - A tool for creating custom Windows ISO images with pre-installed programs"
    )

    parser.add_argument(
        "-c",
        "--config",
        type=str,
        help="Path to configuration file. Default: config.toml",
        default="config.toml",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        help="Path to the output ISO file. Required if '--usb' flag is not provided.",
    )
    parser.add_argument(
        "-u",
        "--usb",
        type=str,
        help="Path to the USB drive to flash the custom image onto. Warning: This will erase all data on the USB drive. Required if '--output' flag is not provided.",
    )
    parser.add_argument(
        "-l",
        "--list-editions",
        type=str,
        help="Displays Windows editions available from a provided WIM or ISO file.",
    )

    args = parser.parse_args()

    if args.list_editions:
        file_path = os.path.abspath(args.list_editions)
        if os.path.isfile(file_path) and (
            (file_ext := file_path[-4:].lower()) in [".iso", ".wim"]
        ):
            if file_ext == ".iso":
                print(f'Mounting iso "{file_path}"...')
                iso_mountpoint = mount_iso(file_path)
                wim_file = f"{iso_mountpoint}\\sources\\install.wim"
            else:
                wim_file = file_path

            try:
                wim_info = list_wim_indexes(wim_file)
                display_wim_editions(wim_info)
            finally:
                if file_ext == ".iso":
                    print(f'Unmounting iso "{file_path}"...')
                    iso_mountpoint = unmount_iso(file_path)
            sys.exit()
        else:
            parser.error("--list-editions takes an ISO or a WIM file as parameter")
    elif not args.output and not args.usb:
        parser.error("At least one of --output or --usb is required.")
    elif args.output and args.usb:
        parser.error("The --output and --usb arguments are mutually exclusive.")

    global CONFIG
    CONFIG = read_toml(args.config)

    if args.output:
        choice = Operations.CREATE_CUSTOM_ISO
    else:
        choice = Operations.CREATE_BOOTABLE_USB

    match choice:
        case Operations.CREATE_CUSTOM_ISO:
            create_custom_iso(CONFIG["general"]["iso"], args.output)
        case Operations.CREATE_BOOTABLE_USB:
            create_bootable_usb(CONFIG["general"]["iso"], args.usb)

    print(
        f"Done! Your {'USB drive' if choice == Operations.CREATE_BOOTABLE_USB else 'custom ISO'} is ready!"
    )
    input("Press enter to continue...")


if __name__ == "__main__":
    main()
