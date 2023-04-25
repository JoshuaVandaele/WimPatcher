import os
import subprocess

from modules.utils import copy_files
from pycdlib import pycdlib


def add_files_to_iso(iso: pycdlib.PyCdlib, source_path: str, iso_path: str) -> None:
    """
    Adds files and directories from a source directory to an ISO file.

    Args:
        iso (pycdlib.PyCdlib): The ISO file to add the files and directories to.
        source_path (str): The path to the source directory.
        iso_path (str): The path to the ISO directory.

    Returns:
        None
    """
    for root, dirs, files in os.walk(source_path):
        for d in dirs:
            abs_dir = os.path.join(root, d)
            rel_dir = os.path.relpath(abs_dir, source_path)
            iso_dir = os.path.join(iso_path, rel_dir).replace("\\", "/")
            iso.add_directory(udf_path=iso_dir)

        for file in files:
            abs_path = os.path.join(root, file)
            rel_path = os.path.relpath(abs_path, source_path)
            iso_path_file = os.path.join(iso_path, rel_path).replace("\\", "/")

            print(abs_path, iso_path_file)
            iso.add_file(abs_path, udf_path=iso_path_file)


def create_iso_from_folder(folder_path: str, iso_path: str) -> None:
    """
    Creates an ISO file from a source directory.

    Args:
        folder_path (str): The path to the source directory.
        iso_path (str): The path to the ISO file to be created.

    Returns:
        None
    """
    iso = pycdlib.PyCdlib()
    iso.new(udf="2.60", interchange_level=4, vol_ident="UDF Volume")

    add_files_to_iso(iso, folder_path, "/")

    iso.write(iso_path)
    iso.close()


def mount_iso(iso_file: str) -> str:
    """
    Mounts an ISO file and returns the drive letter of the mounted drive.

    Args:
        iso_file (str): The path to the ISO file.

    Returns:
        The drive letter of the mounted drive.
    """
    mount_result = subprocess.run(
        [
            "powershell",
            "(Mount-DiskImage",
            "-ImagePath",
            iso_file,
            "-PassThru",
            "|",
            "Get-Volume).DriveLetter",
        ],
        capture_output=True,
        text=True,
    )
    return f"{mount_result.stdout.strip()}:"
    # TODO: add support for `with` statement


def unmount_iso(iso_file: str) -> None:
    """
    Unmounts a previously mounted ISO file.

    Args:
        iso_file (str): The path to the ISO file.

    Returns:
        None
    """
    subprocess.run(
        ["powershell", "Dismount-DiskImage", "-ImagePath", iso_file],
        stdout=subprocess.PIPE,
    )


def extract_iso(iso_file: str, extract_location: str) -> None:
    """
    Extracts the contents of an ISO file to a specified location.

    Args:
        iso_file (str): The path to the ISO file.
        extract_location (str): The path to the directory where the contents of the ISO file should be extracted.

    Returns:
        None
    """
    print(f'Mounting iso "{iso_file}"...')
    iso_mount_path: str = mount_iso(iso_file)

    try:
        print("Extracting iso file...")
        copy_files(iso_mount_path, extract_location)
    finally:
        print(f'Unmounting iso "{iso_file}"...')
        unmount_iso(iso_file)
