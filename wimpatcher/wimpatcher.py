import os
import tempfile

from modules.iso import create_iso_from_folder, extract_iso
from modules.usb import prepare_usb_drive
from modules.utils import Operations, run_as_admin
from modules.wim import delete_other_editions, list_wim_indexes, mount_wim, unmount_wim


def create_custom_iso(iso_file: str):
    with tempfile.TemporaryDirectory() as tmpdir:
        extract_iso(iso_file, tmpdir)

        patch_wim(f"{tmpdir}\\sources\\install.wim")

        print("Repacking...")
        create_iso_from_folder(tmpdir, "out.iso")

        print("Cleaning up...")


def create_bootable_usb(iso_file: str):
    print("Enter the drive letter of your USB drive:")
    drive_letter = input("> ")[:1].upper()
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
        valid_indexes[index] = info
        print(f"[{index}] {info['Name']} ({info['Size']})")
    return valid_indexes


def patch_wim(wim_file: str):
    wim_info = list_wim_indexes(wim_file)

    if len(wim_info) <= 1:
        return
    print("Which edition would you like to use?")
    valid_indexes = display_wim_editions(wim_info)

    if (wim_index := input("> ")) in valid_indexes:
        selection = valid_indexes[wim_index]
    else:
        raise ValueError(f"'{wim_index}' is not a valid selection!")

    delete_other_editions(wim_file, selection)

    print("Mounting the WIM file...")
    wim_mount_path = mount_wim(wim_file)

    try:
        # Do stuff in wim_mount_path here
        with open(wim_mount_path + "\\test.txt", "w") as file:
            file.write("this should appear in the wim file")
    finally:
        print("Unmounting the WIM file...")
        unmount_wim(wim_mount_path)


def main():
    run_as_admin()

    iso_file = os.getcwd() + "\\Win11.iso"

    while True:
        print("Enter the path to the ISO file: ")
        iso_file = input("> ")

        if not os.path.isfile(iso_file):
            print("Error: The specified file path does not exist.")
        else:
            iso_file = os.path.abspath(iso_file)
            break

    print("Choose an option:")
    print(f"[{Operations.CREATE_CUSTOM_ISO}] Create a custom ISO file")
    print(f"[{Operations.CREATE_BOOTABLE_USB}] Create a bootable USB drive")
    choice = input("> ")

    match choice:
        case Operations.CREATE_CUSTOM_ISO:
            create_custom_iso(iso_file)
        case Operations.CREATE_BOOTABLE_USB:
            create_bootable_usb(iso_file)
        case _:
            print(
                f"Invalid choice. Please pick an option between {Operations.CREATE_CUSTOM_ISO} and {Operations.CREATE_BOOTABLE_USB}."
            )
            return

    print(
        f"Done! Your {'USB drive' if choice == Operations.CREATE_BOOTABLE_USB else 'custom ISO'} is ready!"
    )
    input("Press enter to continue...")


if __name__ == "__main__":
    main()
