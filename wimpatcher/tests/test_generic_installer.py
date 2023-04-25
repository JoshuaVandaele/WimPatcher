import os
import shutil
import tempfile
import unittest

from wimpatcher.installers.generic_installer import Installer
from wimpatcher.tests.test_base import TestCaseBase


class TestInstaller(TestCaseBase):
    def setUp(self):
        self.tempdir = tempfile.mkdtemp()

        self.program_name = "Test Program"
        self.installer_file = os.path.join(self.tempdir, "installer_file")
        self.wim_mount_directory = os.path.join(self.tempdir, "wim_mount_directory")
        self.install_location = os.path.join(
            self.wim_mount_directory, "install_location"
        )
        self.parameters = None

        os.makedirs(os.path.join(self.wim_mount_directory, r"Windows\System32\config"))
        shutil.copyfile(
            os.path.join(os.getcwd(), r"wimpatcher\tests\ressources\SOFTWARE"),
            os.path.join(self.wim_mount_directory, r"Windows\System32\config\SOFTWARE"),
        )

        self.installer = Installer(
            self.program_name,
            self.install_location,
            self.installer_file,
            self.wim_mount_directory,
            self.parameters,
        )

    def tearDown(self):
        if os.path.exists(self.tempdir):
            shutil.rmtree(self.tempdir)

    def test_init(self):
        self.assertEqual(self.installer.program_name, self.program_name)
        self.assertEqual(self.installer.install_location, self.install_location)
        self.assertEqual(self.installer.installer_file, self.installer_file)
        self.assertEqual(self.installer.parameters, [])

    def test_install_directory(self):
        os.mkdir(self.installer_file)
        self.installer.install()

        self.assertIsFolder(self.install_location)

    def test_install_file_archive(self):
        shutil.make_archive(self.installer_file, "zip", self.install_location)
        os.rename(f"{self.installer_file}.zip", self.installer_file)
        self.installer.install()

        self.assertIsFolder(self.install_location)

    def test_install_executable(self):
        with open(self.installer_file, "w") as f:
            f.write("dummydata")

        self.installer.install()

        self.assertIsFolder(self.install_location)

    def test_create_shortcut(self):
        shortcut_path = os.path.join(self.install_location, "test.lnk")
        os.mkdir(self.install_location)

        with open(self.installer_file, "w") as f:
            f.write("dummydata")

        Installer.create_shortcut(self.installer_file, shortcut_path)

        self.assertIsFile(shortcut_path)

    def test_install_nonexisting_installer(self):
        installer = Installer(
            program_name=self.program_name,
            install_location=self.install_location,
            installer_file=os.path.join(self.tempdir, "non_existent_file"),
            wim_mount_directory=self.wim_mount_directory,
            parameters=self.parameters,
        )

        with self.assertRaises(ValueError):
            installer.install()


if __name__ == "__main__":
    unittest.main()
