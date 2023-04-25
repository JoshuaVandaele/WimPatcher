import os
import shutil
import subprocess
import tempfile
import threading

from modules.utils import onerror, show_progress


def mount_wim(wim_file: str) -> str:
    """
    Mounts a Windows Imaging Format (WIM) file to a temporary directory.

    Args:
        wim_file (str): The path to the WIM file to be mounted.

    Returns:
        str: The path to the mount point.

    """
    mount_path = tempfile.mkdtemp()
    if not os.path.exists(mount_path):
        os.mkdir(mount_path)

    subprocess.run(["attrib", "-r", wim_file])

    proc = subprocess.Popen(
        [
            "DISM",
            "/Mount-WIM",
            f"/WimFile:{wim_file}",
            "/Index:1",
            f"/MountDir:{mount_path}",
        ],
        stdout=subprocess.PIPE,
        universal_newlines=True,
    )

    stdout_thread = threading.Thread(target=show_progress, args=(proc.stdout,))
    stdout_thread.start()

    proc.wait()
    stdout_thread.join()

    return mount_path
    # TODO: add support for `with` statement


def unmount_wim(wim_mount_path: str) -> None:
    """
    Unmounts a previously mounted Windows Imaging Format (WIM) file and commits changes.

    Args:
        wim_mount_path (str): The path to the mount point of the WIM file.

    Returns:
        None

    """
    proc = subprocess.Popen(
        [
            "DISM",
            "/unmount-wim",
            f"/MountDir:{wim_mount_path}",
            "/commit",
        ],
        stdout=subprocess.PIPE,
        universal_newlines=True,
    )

    stdout_thread = threading.Thread(target=show_progress, args=(proc.stdout,))
    stdout_thread.start()

    proc.wait()
    stdout_thread.join()

    shutil.rmtree(wim_mount_path, onerror=onerror)


def delete_other_editions(wim_file: str, edition_to_keep: dict) -> None:
    """
    Deletes other editions in a WIM file, except the selected edition.

    Args:
        wim_file (str): The path to the WIM file.
        edition_to_keep (dict): A dictionary containing the details of the edition to keep.

    Returns:
        None
    """
    edition_to_keep["Index"] = "1"

    while len(new_info := list_wim_indexes(wim_file)) != 1:
        index_to_remove = next(info["Index"] for info in new_info if info != edition_to_keep)  # type: ignore
        print(
            f"Removing {next(info['Name'] for info in new_info if info != edition_to_keep)}"  # type: ignore
        )
        delete_wim_index(wim_file, index_to_remove)


def list_wim_indexes(wim_file: str) -> list[dict[str, str]]:
    """
    Lists all indexes in a Windows Imaging Format (WIM) file.

    Args:
        wim_file (str): The path to the WIM file.

    Returns:
        A list of dictionaries containing information about the WIM file indexes.

    """
    result = subprocess.run(
        [
            "dism",
            "/get-WimInfo",
            f"/WimFile:{wim_file}",
        ],
        capture_output=True,
        text=True,
    )
    # Given this input:
    # ^
    # ^Deployment Image Servicing and Management tool
    # ^Version: 10.0.25336.1000
    # ^
    # ^Details for image : E:/sources/install.wim
    # ^
    # ^Index : 1
    # ^Name : Windows 11 Home
    # ^Description : Windows 11 Home
    # ^Size : 16,113,912,790 bytes
    # ^
    # ^Index : 2
    # ^...
    # ^
    # ^The operation completed successfully.
    #
    # The process consists of the following steps:
    # 1. Convert the input into a list of strings containing ["Index : 1\nName : ...", "Index : 2\nName : ..."]
    # 2. For each entry in the list, split the string by `\n` to obtain a new list: ["Index : 1", "Name : ..."]
    # 3. For every element in the sublist, split it by `:` to create a list like this: [["Index ", " 1"], ["Name ", " ..."]].
    # 4. Strip each element of the sublist of additional spaces using str.strip, and convert them into tuples: [("Index", "1"), ("Name", "...")]
    # 5. Turn the tuples into a dictionary: {'Index': '1', 'Name': '...'}
    # 6. Append the dictionary to a list and process the next entry until all entries are processed: [{'Index': '1', 'Name': '...'}, {'Index': '2', 'Name': '...'}]
    indexes = result.stdout.split("\n\n")[2:-1]
    return [
        dict(tuple(map(str.strip, kv.split(":"))) for kv in index.split("\n"))
        for index in indexes
    ]


def optimize_wim_file(wim_file: str) -> None:
    old_wim = os.path.join(
        os.path.dirname(wim_file), f"{os.path.basename(wim_file)}.old"
    )
    os.rename(wim_file, old_wim)
    # Exports the index to a new wim file,
    # in which the [DELETED] folder will be gone and the size reduced.
    # (After every dism command the deleted/changed files are saved in the wim inside [DELETED])
    subprocess.run(
        [
            "DISM",
            "/Export-Image",
            f"/SourceImageFile:{old_wim}",
            "/SourceIndex:1",
            f"/DestinationImageFile:{wim_file}",
            "/Compress:max",
            "/Checkintegrity",
        ],
        stdout=subprocess.PIPE,
    )

    os.remove(old_wim)


def optimize_wim_image(wim_mount_path: str):
    subprocess.run(
        [
            "DISM",
            f"/Image:{wim_mount_path}",
            "/Cleanup-Image",
            "/StartComponentCleanup",
            "/ResetBase",
        ],
        # stdout=subprocess.PIPE,
    )


def delete_wim_index(wim_file, index):
    """
    Deletes an index from a Windows Imaging Format (WIM) file.

    Args:
        wim_file (str): The path to the WIM file.
        index (str): The index to be deleted.

    Returns:
        None

    """
    subprocess.run(["attrib", "-r", wim_file])
    subprocess.run(
        [
            "DISM",
            "/Delete-Image",
            f"/ImageFile:{wim_file}",
            f"/Index:{index}",
        ],
        stdout=subprocess.PIPE,
    )
