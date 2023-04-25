import ctypes
import os
import stat
import subprocess
import sys
import threading
import winreg
from enum import StrEnum
from typing import TextIO

import win32api
import win32security


def onerror(func, path, exc_info):
    """
    Error handler for `shutil.rmtree`.

    If the error is due to an access error (read only file)
    it attempts to add write permission and then retries.

    If the error is for another reason it re-raises the error.

    Usage : `shutil.rmtree(path, onerror=onerror)`
    """
    os.chmod(path, stat.S_IWRITE)
    func(path)


class Operations(StrEnum):
    """
    Enum representing supported operations.
    """

    CREATE_CUSTOM_ISO = "1"
    CREATE_BOOTABLE_USB = "2"


def run_as_admin() -> None:
    """
    Re-launches the current script as an administrator if the user is not
    already running the script with administrative privileges.
    """
    if not ctypes.windll.shell32.IsUserAnAdmin():
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, " ".join(sys.argv), None, 1
        )
        sys.exit()


def run_diskpart(commands: list[str]) -> None:
    """
    Executes the specified list of DiskPart commands in a DiskPart session.

    Args:
        commands (List[str]): A list of DiskPart commands to execute.
    """
    diskpart_process = subprocess.Popen(
        ["diskpart"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
    )

    if not diskpart_process.stdin:
        return

    for command in commands:
        diskpart_process.stdin.write(f"{command}\n")

    diskpart_process.stdin.write("exit\n")
    diskpart_process.communicate()


def show_progress(pipe: TextIO):
    """
    Reads and prints the last given information from a given subprocess.PIPE object,
    overwriting the previous line.

    Args:
        pipe (subprocess.PIPE): A subprocess.PIPE object containing progress data.
    """
    line_len = 0
    while True:
        line: str = str(pipe.readline())
        if not line:
            break
        line = line.replace("\n", "")
        progress_info = line.strip()
        print(progress_info, end=(" " * (line_len - len(progress_info))) + "\r")
        line_len = len(progress_info) + 1

    print(" " * line_len, end="\r")


def copy_files(src: str, dest: str) -> None:
    """
    Copies files from the source directory to the destination directory
    using 'robocopy' with specified options.

    Args:
        src (str): The source directory path.
        dest (str): The destination directory path.
    """
    proc = subprocess.Popen(
        [
            "robocopy",
            src,
            dest,
            "/e",
            "/NS",
            "/NC",
            "/NDL",
            "/NJS",
        ],
        stdout=subprocess.PIPE,
        universal_newlines=True,
    )

    stdout_thread = threading.Thread(target=show_progress, args=(proc.stdout,))
    stdout_thread.start()

    # Wait for the subprocess and stdout thread to finish
    proc.wait()
    stdout_thread.join()


def load_registry_hive(hive_path: str, subkey: str) -> None:
    """
    Loads a registry hive file into the system registry at a specified subkey
    location, enabling "SeRestorePrivilege" privilege as needed.

    Args:
        hive_path (str): The path of the registry hive file to be loaded.
        subkey (str): The registry subkey under which to load the hive.
    """
    # I do not know how this works exactly, but this piece of code gives us the "SeRestorePrivilege" privilege which is required to load hives into the registry
    priv_flags = win32security.TOKEN_ADJUST_PRIVILEGES | win32security.TOKEN_QUERY
    hToken = win32security.OpenProcessToken(win32api.GetCurrentProcess(), priv_flags)
    privilege_id = win32security.LookupPrivilegeValue(None, "SeRestorePrivilege")  # type: ignore
    win32security.AdjustTokenPrivileges(
        hToken, 0, [(privilege_id, win32security.SE_PRIVILEGE_ENABLED)]  # type: ignore
    )

    # Load the given hive
    winreg.LoadKey(winreg.HKEY_LOCAL_MACHINE, subkey, hive_path)


def unload_registry_hive(subkey: str) -> None:
    """
    Unloads a registry hive from the system registry at a specified subkey location.

    Args:
        subkey (str): The registry subkey of the hive to be unloaded.
    """
    # Unload the hive. Apparently winreg doesn't propose to do that,
    # and I haven't found any other library capable of manipulating the registry,
    # so we're doing calls to C functions
    advapi32 = ctypes.WinDLL("Advapi32.dll")

    # Define the necessary types
    HKEY = ctypes.c_void_p
    LPCTSTR = ctypes.c_wchar_p

    # Define the RegUnLoadKeyW function
    RegUnLoadKeyW = advapi32.RegUnLoadKeyW
    RegUnLoadKeyW.restype = ctypes.c_long
    RegUnLoadKeyW.argtypes = [HKEY, LPCTSTR]

    # Open the HKEY_LOCAL_MACHINE key
    hkey_local_machine = HKEY(0x80000002)

    result = RegUnLoadKeyW(hkey_local_machine, subkey)

    if result != 0:
        e = OSError(
            f"Could not unload the registry hive at HKEY_LOCAL_MACHINE/{subkey}"
        )
        e.winerror = result
        e.errno = result
        raise e


def add_string_to_registry(
    key: "winreg._KeyType", sub_key: str, key_name: str, value: str
) -> None:
    """
    Adds a string value to the specified registry key and subkey.

    Args:
        key (winreg._KeyType): The registry key to add the value to.
        sub_key (str): The registry subkey to add the value to.
        key_name (str): The name of the registry value to be added.
        value (str): The string value to be set for the registry value.
    """
    # Add the key and value to RunOnce
    new_key = winreg.OpenKey(
        key,
        sub_key,
        0,
        winreg.KEY_SET_VALUE,
    )
    winreg.SetValueEx(new_key, key_name, 0, winreg.REG_SZ, value)
    winreg.CloseKey(new_key)


def add_key_to_run_once_hive(hive_path: str, key_name: str, value: str) -> None:
    """
    Adds a key to the RunOnce section of an offline SOFTWARE registry hive.

    Args:
        hive_path (str): The path of the offline SOFTWARE registry hive.
        key_name (str): The name of the registry key to be added to RunOnce.
        value (str): The command to be executed when the RunOnce key is triggered.
    """
    subkey = "WIM_SOFTWARE"

    load_registry_hive(hive_path, subkey)

    try:
        add_string_to_registry(
            winreg.HKEY_LOCAL_MACHINE,
            r"WIM_SOFTWARE\Microsoft\Windows\CurrentVersion\RunOnce",
            key_name,
            value,
        )
    finally:
        unload_registry_hive(subkey)
