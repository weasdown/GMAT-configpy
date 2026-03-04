# Downloads and compiles the Xerces library that is a GMAT dependency.
# This should be run from the [GMAT]/depends folder.

from globals import osx_min_version, osx_sdk
import os
import utils as u
from utils import download_file, set_env_variables, Platform
from pathlib import Path
import subprocess


def _compile_xerces():
    """Configures and compiles the folder extracted by `_extract_xerces()`."""
    pass


def _download_xerces(version: str) -> Path:
    """Downloads the Xerces archive file."""
    xerces_url: str = f'https://archive.apache.org/dist/xerces/c/3/sources/xerces-c-{version}.tar.gz'
    download_file(xerces_url)
    archive_name = xerces_url.rsplit('/', 1)[-1]
    return Path(os.getcwd())/archive_name


def _extract_xerces(archive: Path) -> None:
    """Extracts the archive file downloaded by `_download_xerces()`."""
    u.extract(archive)


if __name__ == '__main__':
    xerces_version: str = '3.2.2'

    set_env_variables()

    depends: Path = u.directories.depends

    # FIXME: make cross-platform
    xerces_path = depends/'xerces'
    xerces_build_path = f'{xerces_path}/linux-build'
    xerces_install_path = f'{xerces_path}/linux-install'

    u.cd(depends, debug=True)

    # TODO add test file that if present, stops this before starting

    archive = _download_xerces(xerces_version)

    _extract_xerces(archive)
    versioned_folder_name = str(archive).replace('.tar.gz', '')
    # Rename 'xerces-c-3.2.2' to 'xerces'.
    os.rename(versioned_folder_name, 'xerces')

    # Remove downloaded archive
    u.rm(Path(depends/'xerces-c-3.2.2.tar.gz'))

    # Make build and install directories
    os.mkdir(Path(depends)/'xerces'/'linux-build')
    os.mkdir(Path(depends)/'xerces'/'linux-install')

    u.cd(Path(depends/'xerces'/'linux-build'))

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

        # Configure Xerces.
        print(
            f'Configuring Xerces {xerces_version} {configuration} library. This could take a while...')
        configure_debug = f'../configure --disable-shared --disable-netaccessor-curl --disable-transcoder-icu --disable-msgloader-icu CFLAGS="{flags}" CXXFLAGS="{flags}" --prefix="{str(depends)}/xerces/linux-install" > "../../logs/xerces_configure_{configuration}.log" 2>&1'
        p = subprocess.run(configure_debug, capture_output=True, shell=True)

        # Make Xerces.
        print(f'\nMaking {configuration} library...\n')
        p = subprocess.run(
            f'make -j4 > "../../logs/xerces_make_{configuration}.log" 2>&1', capture_output=True, shell=True)

        # Make install Xerces.
        print(f'Make installing {configuration} library...\n')
        p = subprocess.run(
            f'make install -j4 > "../../logs/xerces_make_install_{configuration}.log" 2>&1', capture_output=True, shell=True)

    build_xerces('debug')

    # Rename debug library file to avoid being overwritten when making release configuration.
    os.rename(f'{xerces_install_path}/lib/libxerces-c.a',
              f'{xerces_install_path}/lib/libxerces-cd.a')

    # Clean build to prepare for making release configuration.
    subprocess.run('make clean > /dev/null 2>&1',
                   capture_output=True, shell=True)

    build_xerces('release')
