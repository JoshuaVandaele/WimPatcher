import os
import shutil
import subprocess
import tempfile
from pathlib import Path

import patoolib

from wimpatcher.modules.utils import add_key_to_run_once_hive


class Installer:
    def __init__(
        self: "Installer",
        program_name: str,
        install_location: str,
        installer_file: str,
        wim_mount_directory: str,
        parameters: None | list[str] = None,
    ) -> None:
        """A class to handle installation of software.

        Args:
            program_name (str): The name of the program being installed.
            install_location (str): The path to the directory where the program should be installed.
            installer_file (str): The path to the installer file.
            wim_mount_directory (str): WIM mount directory of the WIM where we will be installing the program.
            parameters (None | list[str], optional): A list of command-line parameters to pass to the installer, if it's an executable. Defaults to None.
        """
        self.program_name: str = program_name
        self.install_location: str = os.path.abspath(install_location)
        self.installer_file: str = installer_file
        self.wim_mount_directory: str = os.path.abspath(wim_mount_directory)
        self.parameters: list[str] = parameters or []

        if self.wim_mount_directory not in self.install_location:
            raise ValueError(
                f"install_location must be in wim_mount_directory! Values provided: {self.install_location} and {self.wim_mount_directory}"
            )

    def install(self: "Installer"):
        """Install the program at the specified location."""
        if not os.path.exists(self.install_location):
            os.makedirs(self.install_location)

        if os.path.isdir(self.installer_file):
            if os.path.exists(self.install_location):
                shutil.rmtree(self.install_location)
            shutil.copytree(self.installer_file, self.install_location)
        elif os.path.isfile(self.installer_file):
            try:
                # If the file is an archive (ZIP, RAR, etc), extract it at the install location
                patoolib.extract_archive(
                    self.installer_file, outdir=self.install_location
                )
            except patoolib.util.PatoolError:
                shutil.move(self.installer_file, self.install_location)
                add_key_to_run_once_hive(
                    rf"{self.wim_mount_directory}\Windows\System32\config\SOFTWARE",
                    f"install {self.program_name}",
                    rf"C:\{self.install_location.removeprefix(self.wim_mount_directory)}",
                )
        else:
            raise ValueError(f"'{self.installer_file}' is not a file or a folder!")

    @staticmethod
    def create_shortcut(src: str, dest: str):
        """Create a shortcut to a program.

        Args:
            src (str): The path to the program executable.
            dest (str): The path where the shortcut should be created.
        """
        vbs_script = f"""
Set WshShell = WScript.CreateObject("WScript.Shell")
Set Shortcut = WshShell.CreateShortcut("{dest}")

Shortcut.TargetPath = "{src}"
Shortcut.WorkingDirectory = "{Path(src).parent}"
Shortcut.WindowStyle = 1
Shortcut.IconLocation = "{src}, 0"

Shortcut.Save
        """
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".vbs", delete=False
        ) as vbs_file:
            vbs_file.write(vbs_script)
            vbs_file.flush()

        try:
            subprocess.run(
                ["cscript.exe", "//NoLogo", vbs_file.name],
                check=True,
                capture_output=True,
            )
        finally:
            os.unlink(vbs_file.name)
