# Utility functions for downloading and extracting archives and running commands.

import os
import shutil
import subprocess
import sys
import tarfile
from enum import Enum
from pathlib import Path


def run_command(command: str, capture_output: bool = False, check: bool = False, shell: bool = True,
                stdin: subprocess._FILE = None, stdout: subprocess._FILE = None, stderr: subprocess._FILE = None,
                text: bool = False, debug: bool = False) -> subprocess.CompletedProcess:
    """Runs a shell command and returns its `subprocess.CompletedProcess`."""
    if debug:
        print(f'Running command "{command}" in "{os.getcwd()}"')
    process: subprocess.CompletedProcess = subprocess.run(
        command, capture_output=capture_output, check=check, shell=shell, stdin=stdin, stdout=stdout, stderr=stderr,
        text=text)
    return process


class _Directories:
    def __init__(self) -> None:
        """Defines useful directories."""
        _user = run_command('whoami', capture_output=True,
                            text=True).stdout.rstrip()

        self._gmat: Path = Path(f'/home/{_user}/dev/non-OH/gmat/GMAT-R2025a')
        self._gmat_git: Path = Path(f'/home/{_user}/dev/non-OH/gmat/gmat-git')
        self._depends: Path = (self._gmat_git / 'depends')

    @property
    def depends(self) -> Path:
        return self._depends

    @property
    def gmat(self) -> Path:
        return self._gmat

    @property
    def gmat_git(self) -> Path:
        return self._gmat_git

    def set_variables(self) -> None:
        """Sets environment variables for the directories."""
        os.environ['GMAT_GIT'] = str(self.gmat_git)
        os.environ['depends'] = str(self.depends)
        os.environ['GMAT'] = str(self.gmat)


directories: _Directories = _Directories()


class Platform(Enum):
    """Defines OS platforms for easier comparison."""
    Windows = 'win32'
    macOS = 'macosx'
    Linux = 'linux'

    @classmethod
    def current(cls) -> Platform:
        match sys.platform:
            case 'win32':
                return Platform.Windows
            case 'linux':
                return Platform.Linux
            case 'macosx':
                return Platform.macOS
            case _:
                raise RuntimeError(
                    f'Platform "{sys.platform}" is not recognised.')


def cd(directory: Path, debug: bool = False) -> None:
    """Change directory to `directory`."""
    os.chdir(str(directory))
    if debug:
        print(f'\nSwitched to {directory}\n')


def download_file(url: str, save_name: str = '', debug: bool = False) -> int:
    """Downloads a file from a url and saves it to the current working directory."""
    if debug:
        print(
            f'Downloading from "{url}" and saving as "{os.getcwd()}/{save_name}".')
    # If no save_name was provided, wget will use the end of the url by default.
    save_argument: str = '' if not save_name else f'-O {save_name} '

    if Platform.current() == Platform.Windows:
        return run_command(f'curl -L {url} > {save_name}', capture_output=True, check=True).returncode

    # Linux or macOS
    else:
        return run_command(
            f'wget -q --show-progress {save_argument}{url}', check=True).returncode


def extract(archive: Path, output_path: str = '') -> None:
    """
    Unzips a .zip or .tar file in a given directory to the current directory, or to a given output directory if specified.

    .tar files can be .tar, .tar.gz or .tar.bz2.

    :param archive: an archive file to extract.
    :type archive: str

    :param output_path: an optional path to extract the archive to that if given must be relative to the current working directory. Defaults to the current working directory.
    :type output_path: str

    :return: None
    :rtype: NoneType
    """
    platform: Platform = Platform.current()
    extension = archive.suffix

    not_implemented_on_platform = NotImplementedError(
        f'Extracting of {extension} files on {platform.name} is not yet implemented.')

    if extension == '.zip':
        if platform == Platform.Windows:
            seven_zip_exe = f'{directories.depends}/bin/7za/7za.exe'
            output_path_arg: str = '' if output_path is None else f'-o"./{output_path}" '
            run_command(
                f'{seven_zip_exe} x {archive} -r {output_path_arg}> nul')
        else:
            raise not_implemented_on_platform

    elif extension == '.bz2':
        if platform == Platform.Windows:
            with tarfile.open(archive, 'r:bz2') as tar:
                tar.extractall(
                    filter='data', path=output_path if output_path else '.')
        elif platform == Platform.Linux:
            run_command(f'tar xjf {archive}')

    elif extension == '.gz':
        if platform == Platform.Windows:
            raise not_implemented_on_platform
        else:  # Linux or macOS
            with tarfile.open(archive, 'r:gz') as tar:
                tar.extractall(filter='data')

    else:
        raise ValueError(f'Archives with the "{extension}" extension cannot be extracted using extract().\n'
                         f'\nExtraction variables in extract():\n'
                         f'\t- archive: "{archive}"\n'
                         f'\t- extension: "{extension}"\n'
                         f'\t- output_path: "{output_path}"\n')


def rm(item: Path, debug: bool = False) -> None:
    """Removes a file or directory."""
    if debug:
        print(f'\nRemoving "{item.name}" from "{os.getcwd()}"\n')

    # raise NotImplementedError('rm() function is not yet working.')

    # # FIXME below is not working - files/folders are not deleted.
    if item.is_dir():
        shutil.rmtree(str(item))
    elif item.is_file():
        os.remove(item)
    else:
        raise NotImplementedError


def set_env_variables() -> None:
    """Sets convenience environment variables for GMAT configuring."""
    directories.set_variables()
    print('All environment variables set.\n')


if __name__ == '__main__':
    pass
