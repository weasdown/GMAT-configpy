# Resets the 'depends' folder to its default state, removing all configured dependencies.

import argparse
import os
import sys
from pathlib import Path
import shutil


def configure_argparse() -> argparse.Namespace:
    """Configures the argument parser and returns the received arguments."""
    help_description = "A Python program to reset GMAT's 'depends' folder to its default contents."
    parser = argparse.ArgumentParser(description=help_description)

    # Optional argument for path to depends folder. Defaults to depends within the GMAT folder specified by the 'GMAT' environment variable.
    gmat_env: str = os.environ.get('GMAT')  # 'GMAT' environment variable. None if not set.
    d_required: bool = True
    if gmat_env is not None:
        gmat_path: Path = Path(gmat_env).expanduser().resolve()
        default = gmat_path / 'depends'
        d_required = False
    else:
        default = ...

    parser.add_argument('-d', '--depends', help='Path to GMAT/depends folder.', type=Path, required=d_required,
                        default=default)

    # Optional flag to force deletion (similar to rm -f).
    parser.add_argument('-f', '--force', help='Proceed with deletions without asking for permission.',
                        action='store_true')

    # Read arguments from command line.
    arguments = parser.parse_args()

    # No -d argument was given, so we must be able to derive the depends path from the 'GMAT' environment variable.
    if arguments.depends is None:
        gmat: Path = Path(gmat_env)
        arguments.depends = gmat / 'depends'

    return arguments


def delete_non_defaults(items_to_delete: list[Path]) -> None:
    """Deletes any non-default items in the depends folder."""
    if not items_to_delete:
        print('\nNo items to delete.')
        return

    print(f'\nDeleting non-default items from {depends}...')

    print(f'Will delete the following: {[str(item) for item in items_to_delete]}')

    for item in items_to_delete:
        if item.is_file():
            os.remove(item)
        elif item.is_dir():
            shutil.rmtree(item)
        else:
            raise NotImplementedError
        print(f'\t- Deleted {item}')


if __name__ == '__main__':
    # Default contents of the depends folder.
    default_contents: list[Path] = [Path(item) for item in
                                    [
                                        'bin',  # Directory
                                        'CMakeLists.txt',
                                        'CMakeModules',  # Directory
                                        'configure.py',
                                        'configure-ORIGINAL.py',
                                        '.gitignore'
                                    ]]

    # Configure argument parsing.
    args = configure_argparse()

    # Path to depends folder.
    depends: Path = args.depends

    # Whether to continue the deletion without asking for permission. True if the -f flag was used.
    force: bool = args.force

    os.chdir(depends)  # Ensure we are starting in the depends folder.

    contents: list[Path] = [Path(item) for item in os.listdir()]  # Current contents of the depends folder.

    print(f'Current contents of depends folder:')
    for f in contents:
        print(f'\t- {f}')

    to_delete: list[Path] = [f for f in contents if f not in default_contents]  # Files/directories to be deleted.

    # The user has opted to continue the deletion without first reviewing depends's contents.
    if force:
        delete_non_defaults(to_delete)

    # No -f/--force argument was given, so we have to get the user's permission to continue the deletion.
    else:
        check_continue: str = input(
            '\nThe following files/directories will be deleted. Do you want to continue? [y/N] ').lower()

        # Permission has been given
        if check_continue == 'y':
            delete_non_defaults(to_delete)
        # If user specified n/N or didn't give an input, permission has not been given.
        else:
            sys.exit(0)
