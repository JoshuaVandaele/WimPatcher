import pathlib

from modules.iso import extract_iso
from modules.utils import copy_files, run_diskpart


def format_usb_drive(drive_letter: str) -> None:
    """
    Formats a USB drive using the diskpart command line tool.

    Args:
        drive_letter (str): The drive letter assigned to the USB drive.

    Returns:
        Any: The output of the diskpart command.

    """
    commands: list[str] = [
        "list disk",
        f"select volume {drive_letter}",
        f"remove letter={drive_letter}",
        "clean",
        "create partition primary",
        "select partition 1",
        "active",
        "format fs=ntfs quick",
        f"assign letter={drive_letter}",
        "exit",
    ]

    run_diskpart(commands)


def prepare_usb_drive(iso_file: str, drive_path: str) -> None:
    """
    Prepares a USB drive for Windows installation by formatting it and copying the necessary files.

    Args:
        iso_file (str): The path to the Windows ISO file.
        drive_letter (str): The drive letter assigned to the USB drive.

    Returns:
        None

    Raises:
        ValueError: If the drive letter matches the home drive, as this would overwrite important files.
    """
    home_drive = pathlib.Path.home().drive
    if drive_path == home_drive:
        raise ValueError(f"USB Drive cannot be '{home_drive}'")

    print("Cleaning and formatting the USB drive...")
    format_usb_drive(drive_path[1])

    print("Copying files to the USB drive...")
    extract_iso(iso_file, drive_path)
