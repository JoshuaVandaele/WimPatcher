# WimPatcher

## ⚠️ This tool is still in developement, and features listed here are potentially not developed yet

WimPatcher is a tool for creating custom Windows ISO images with pre-installed programs. It automates the process of patching a Windows installation image (WIM) file with additional drivers, updates, configuration, and software. With WimPatcher, you can create a pre-configured Windows installation media that includes all the software you need.

## Getting Started

To use WimPatcher, you'll need to have Python 3.8 or later installed on your system. You can download Python from the official website.

Once you have Python installed, you can install the required dependencies by running the following command in a terminal:

```bash
pip install -r requirements.txt
```

## Usage

To use WimPatcher, you'll need to provide a Windows ISO file, which can be obtained by running CreateISO.bat

You can create a configuration file by copying and editing the `config.example.toml` file. The configuration file is a TOML file that lists the software and drivers you want to include in the custom image. If you don't provide a configuration file as parameter, WimPatcher will look for a file named `config.toml` in the current directory.

### Creating a patched ISO file

To create a patched ISO file, run the following command:

```sh
python wimpatcher.py [--config /path/to/config.toml] --output "/path/to/windows_patched.iso"
```

This will create a new ISO file at `/path/to/windows_patched.iso` that includes all the software and drivers listed in the configuration file.

### Flashing the custom image onto a USB drive

To flash the custom image onto a USB drive, run the following command:

```sh
python wimpatcher.py [--config /path/to/config.toml] --usb "E:"
```

This will flash the custom image onto the USB drive located at "E:". Warning: This will erase all data on the USB drive.

## List of supported software

- None yet

## Current state of the project

- [ ] Accept command-line arguments
- [x] Create a layout for the configuration file
- [ ] Use said configuration file
- [x] Unmount/Mount
  - [x] ISO files
  - [x] WIM files
  - [ ] Add support to `with` statements for mounting/unmounting
- [x] Save to ISO or USB key
- [x] Apply modifications to the WIM file
- [ ] Add support for installing drivers
- [ ] Add support for installing updates
- [x] Add support for generic software installation
- [ ] Add support for the following software:
  - Dev tools
    - [ ] Git
    - [ ] Python
    - [ ] Rust
    - [ ] NodeJS
    - [ ] Lua
    - [ ] HxD
    - [ ] AndroidStudio
    - [ ] Visual Studio Code
    - [ ] Visual Studio 2022 Community
  - Power user software
    - [ ] 7zip
    - [ ] WinSCP
    - [ ] WinDirStat
    - [ ] CheatEngine
    - [ ] qBittorrent
    - [ ] AutoHotKey
    - [ ] HWiNFO
  - User Software
    - [ ] LibreOffice
    - [ ] ShareX
    - [ ] VideoLAN
    - [ ] Firefox
    - [ ] Google Drive
    - [ ] Discord
    - [ ] Discord Canary
    - [ ] Dolphin Emulator
    - [ ] Steam
    - [ ] Krita

## Contributing

Contributions to WimPatcher are welcome! If you find a bug or want to suggest an improvement, please open an issue or submit a pull request.

## License

WimPatcher is licensed under the GPLv3 License. See the LICENSE file for more information.
