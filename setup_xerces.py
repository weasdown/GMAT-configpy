# Downloads and compiles the Xerces library that is a GMAT dependency.
# This should be run from the [GMAT]/depends folder.

import os
import subprocess
from pathlib import Path

import utils as u
from globals import osx_min_version, osx_sdk
from utils import download_file, set_env_variables, Platform


def _compile_xerces():
    """Configures and compiles the folder extracted by `_extract_xerces()`."""
    # Make build and install directories
    os.makedirs(xerces_build_path, exist_ok=True)
    os.makedirs(xerces_install_path, exist_ok=True)

    # Set and make path for logs.
    logs_path = depends / 'logs' / 'xerces'
    os.makedirs(logs_path, exist_ok=True)

    # Extra flags needed for macOS.
    macos_flags = '' if Platform.current() != Platform.macOS \
        else f'-mmacosx-version-min={osx_min_version} --sysroot={osx_sdk}'

    def build_xerces(configuration: str) -> None:
        # C flags for debug and release versions of Xerces.
        if configuration == 'debug':
            flags = f'-O0 -g -fPIC {macos_flags}'
        elif configuration == 'release':
            flags = f'-O2 -fPIC {macos_flags}'
        else:
            raise AttributeError(
                f'Configuration "{configuration}" is not recognised for Xerces. Please use "debug" or "release".')

        # Configure and make/make install commands must be run in build path.
        u.cd(xerces_build_path)

        # Configure Xerces.
        print(
            f'\nConfiguring Xerces {xerces_version} {configuration} library. This could take a while...')
        configure_command = f'../configure --disable-shared --disable-netaccessor-curl --disable-transcoder-icu --disable-msgloader-icu CFLAGS="{flags}" CXXFLAGS="{flags}" --prefix="{str(depends)}/xerces/linux-install" > "{logs_path}/xerces_configure_{configuration}.log" 2>&1'
        subprocess.run(configure_command, capture_output=True, shell=True)

        # Make Xerces.
        print(f'\nMaking {configuration} library...\n')
        subprocess.run(
            f'make -j4 > "{logs_path}/xerces_make_{configuration}.log" 2>&1', capture_output=True, shell=True)

        # Make install Xerces.
        print(f'Make installing {configuration} library...\n')
        subprocess.run(
            f'make install -j4 > "{logs_path}/xerces_make_install_{configuration}.log" 2>&1', capture_output=True,
            shell=True)

    build_xerces('debug')  # Build debug configuration.

    # Rename debug library file to avoid being overwritten when making release configuration.
    os.rename(f'{xerces_install_path}/lib/libxerces-c.a',
              f'{xerces_install_path}/lib/libxerces-cd.a')

    # Clean build to prepare for making release configuration.
    subprocess.run('make clean > /dev/null 2>&1',
                   capture_output=True, shell=True)

    build_xerces('release')  # Build release configuration.

    # Remove build folder - no longer required.
    os.chdir(depends)
    u.rm(xerces_build_path)


def _download_xerces(version: str) -> Path:
    """Downloads the Xerces archive file."""
    xerces_url: str = f'https://archive.apache.org/dist/xerces/c/3/sources/xerces-c-{version}.tar.gz'
    download_file(xerces_url)
    archive_name = xerces_url.rsplit('/', 1)[-1]  # 'xerces-c-{version}.tar.gz'
    return Path(os.getcwd()) / archive_name


def _extract_xerces(archive: Path) -> None:
    """Extracts the archive file downloaded by `_download_xerces()`."""
    u.extract(archive)


if __name__ == '__main__':
    xerces_version: str = '3.2.2'

    set_env_variables()

    depends: Path = u.directories.depends

    # FIXME: make cross-platform
    xerces_path = depends / 'xerces'
    xerces_build_path = xerces_path / 'linux-build'
    xerces_install_path = xerces_path / 'linux-install'

    # Switch to depends folder.
    u.cd(depends)

    # TODO add test file that if present, stops this before starting

    archive = _download_xerces(xerces_version)  # Download the xerces archive.

    _extract_xerces(archive)  # Extract the downloaded archive.
    u.rm(archive)  # Remove downloaded archive.

    # Rename 'xerces-c-3.2.2' folder to 'xerces'.
    versioned_folder_name = str(archive).replace(
        '.tar.gz', '')  # 'xerces-c.3.2.2'
    os.rename(versioned_folder_name, 'xerces')

    # Compile Xerces's debug and release configurations.
    _compile_xerces()

    print('Xerces setup complete!\n')
