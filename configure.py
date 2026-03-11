# Downloads and compiles all core GMAT dependencies.

import os
import platform as mac_plat
import shutil
import struct
import subprocess
import sys
import tarfile
from pathlib import Path

import utils as u
from globals import osx_min_version, osx_sdk
from utils import download_file, set_env_variables, Platform


# TODO copy improvements from config-cmdline.py then make config-cmdline refer to this

# Load the Visual Studio path settings
def setup_windows():
    # 64-bit; change to x86 for 32-bit # TODO set vs_arch based on architecture bits
    vs_arch = 'x86_amd64'
    vs_tools = f'vs{vc_major_version}0comntools'
    if vs_version >= 2017:
        vs_path_base: str = f'{os.getenv("ProgramFiles")}/Microsoft Visual Studio/{str(vs_version)}'

        # Check which edition of Visual Studio is installed
        if os.path.exists(f'{vs_path_base}/Enterprise'):
            vs_path = f'{vs_path_base}/Enterprise/Common7/Tools'
        elif os.path.exists(f'{vs_path_base}/Professional'):
            vs_path = f'{vs_path_base}/Professional/Common7/Tools'
        elif os.path.exists(f'{vs_path_base}/Community'):
            vs_path = f'{vs_path_base}/Community/Common7/Tools'
        elif os.path.exists(f'{vs_path_base}/WDExpress'):
            vs_path = f'{vs_path_base}/WDExpress/Common7/Tools'
        else:
            sys.exit(
                "Could not find suitable Visual Studio development environment.")

        syscall: str = f'{vs_path}/../../VC/Auxiliary/Build/vcvarsall.bat'

    elif vs_version <= 2015:
        vs_path = os.getenv(vs_tools)
        syscall = f'{vs_path}/../../VC/vcvarsall.bat'

    else:
        raise ValueError(
            f'Visual Studio version not recognised - {vs_version}.')

    vs_env_command = f'\"{syscall}\" {vs_arch} & set > vsEnvironment.txt'
    os.system(vs_env_command)

    # Now parse the VC environment
    with open('vsEnvironment.txt', 'r') as f:
        env = f.read().splitlines()
        for line in env:
            pair = line.split('=', 1)
            # print ("--> Setting " + pair[0] + " to " + pair[1])
            os.environ[pair[0]] = pair[1]

    # and delete the temporary settings file
    os.remove('vsEnvironment.txt')

    # Add CMake to path
    sys.path.append('C:/Program Files/CMake/bin')

    print("\nWindows initial setup complete\n")


def download_depends():
    """Download GMAT dependencies."""

    def download_complete(name: str) -> None:
        print(f'{name} download complete!\n')

    def download_xerces():
        # Download xerces if it doesn't already exist
        if os.path.exists(xerces_path):
            print('Xerces already downloaded')
            return

        os.chdir(depends)

        # Download and extract xerces
        print(f'\nDownloading Xerces-C {xerces_version}...')
        xerces_url: str = f'https://archive.apache.org/dist/xerces/c/3/sources/xerces-c-{xerces_version}.tar.gz'
        download_file(xerces_url, 'xerces.tar.gz')
        with tarfile.open('xerces.tar.gz', 'r:gz') as tar:
            tar.extractall(filter='data')
        os.remove('xerces.tar.gz')

        # Rename the extracted xerces directory to be the proper path
        xerces_version_folder = f'xerces-c-{xerces_version}'
        xerces_folder_simple = os.path.basename(os.path.normpath(xerces_path))
        os.rename(xerces_version_folder, xerces_folder_simple)
        download_complete('Xerces')

    def download_wxwidgets():
        if os.path.exists(f'{wxWidgets_path}/wxWidgets-{wx_version}'):
            print('wxWidgets already downloaded')
            return

        # Download wxWidgets if it doesn't already exist
        else:
            # Create & change directories
            if not os.path.exists(wxWidgets_path):
                os.mkdir(wxWidgets_path)
            os.chdir(wxWidgets_path)

            # Download wxWidgets source
            print(f'\nDownloading wxWidgets {wx_version}...')
            wx_url: str = f'https://github.com/wxWidgets/wxWidgets/releases/download/v{wx_version}/wxWidgets-{wx_version}.tar.bz2'
            wx_save_file: Path = Path('wxWidgets.tar.bz2')
            download_file(wx_url, str(wx_save_file))
            u.extract(wx_save_file)
            u.rm(wx_save_file)

            # Make sure wxWidgets was downloaded
            if not os.path.exists(f'{wxWidgets_path}/wxWidgets-{wx_version}'):
                raise RuntimeError(
                    f'Error in wxWidgets-{wx_version} download.')

            download_complete('wxWidgets')

    def download_cspice():
        # Download CSPICE if it doesn't already exist
        if os.path.exists(cspice_path):
            print('CSPICE already downloaded')
            return

        # Create & change directories
        os.makedirs(cspice_path, exist_ok=True)
        os.chdir(cspice_path)

        cspice_type: str = 'PC_Linux_GCC'

        print(f'\nDownloading {cspice_bit}-bit CSPICE {cspice_version}...')
        if platform == Platform.Windows:
            # Download and extract Spice for Windows (32/64-bit)
            cspice_url: str = f'http://naif.jpl.nasa.gov/pub/naif/misc/toolkit_{cspice_version}/C/PC_Windows_VisualC_{cspice_bit}bit/packages/cspice.zip'
            save_name: Path = Path('cspice.zip')
            download_file(cspice_url, str(save_name))
            u.extract(save_name)
            # FIXME: folder name not being set correctly (not cspice64)
            os.rename('cspice', f'{cspice_dir}')
            os.remove('cspice.zip')

        else:  # Platform is not Windows
            if platform == Platform.macOS:
                cspice_type = 'MacIntel_OSX_AppleC'

            # Download and extract Spice for Mac/Linux (32/64-bit)
            cspice_url = f'https://naif.jpl.nasa.gov/pub/naif/misc/toolkit_{cspice_version}/C/{cspice_type}_{cspice_bit}bit/packages/cspice.tar.Z'
            download_file(cspice_url, 'cspice.tar.Z')
            os.system('gzip -d cspice.tar.Z')
            os.system('tar -xf cspice.tar')
            os.system(f'mv cspice {cspice_dir}')
            os.remove('cspice.tar')

        download_complete('CSPICE')

    def download_swig():
        # Download SWIG if it doesn't already exist
        # Check platform-appropriate path
        if os.path.exists(swig_dir):
            print('SWIG already downloaded')
            return

        # Create & change directories
        os.chdir(depends)
        os.makedirs(f'{depends}/swig', exist_ok=True)
        os.makedirs(swig_path, exist_ok=True)  # Duplication?
        os.chdir(swig_path)

        print(f'\nDownloading SWIG {swig_version}...')
        # Windows build
        if platform == Platform.Windows:
            # Download and extract SWIG for Windows
            save_name: Path = Path('swig.zip')
            swig_url = f'http://download.sourceforge.net/swig/swigwin-{swig_version}.zip'
            download_file(swig_url, str(save_name))
            u.extract(save_name)
            os.rename(f'swigwin-{swig_version}', 'swigwin')
            os.remove(save_name)

        # macOS or Linux build
        else:
            # Download and extract SWIG for Mac/Linux
            save_name: Path = Path('swig.tar.gz')
            swig_url = f'https://downloads.sourceforge.net/project/swig/swig/swig-4.2.0/swig-4.2.0.tar.gz'
            download_file(swig_url, str(save_name))
            u.extract(save_name)
            os.system(f'mv swig-{swig_version} swig')
            os.remove(swig_path / save_name)

            # [GMT-6892] Download PCRE into SWIG directory
            print(f'\nDownloading PCRE {pcre_version} for use with SWIG...')
            os.chdir(swig_dir)
            pcre_url: str = f'https://sourceforge.net/projects/pcre/files/pcre/{pcre_version}/{pcre_filename}/download'
            download_file(pcre_url, pcre_filename)

        download_complete('SWIG')

    def download_java():
        # Download Java if it doesn't already exist
        if os.path.exists(java_path):
            print('Java already downloaded')
            return

        # Create & change directories
        os.makedirs(java_path, exist_ok=True)
        os.chdir(java_path)

        java_major_version = java_version.split('.')[0]
        java_full_version = f'{java_version}+{java_update}'

        if platform == Platform.macOS:
            java_os_name = 'mac'
        elif platform == Platform.Windows:
            java_os_name = 'windows'
        else:
            java_os_name = 'linux'

        java_base_url = f'https://github.com/AdoptOpenJDK/openjdk{java_major_version}-binaries/releases/download/jdk-{java_full_version}'
        extension: str = 'zip' if platform == Platform.Windows else 'tar.gz'
        java_url = f'{java_base_url}/OpenJDK{java_major_version}U-jdk_x64_{java_os_name}_hotspot_{java_version}_{java_update}.{extension}'
        downloaded_file: Path = Path(f'jdk.{extension}')

        print(f'\nDownloading Java JDK {java_full_version}...')
        # Windows download
        if platform == Platform.Windows:
            # Download and extract AdoptOpenJDK for Windows
            download_file(java_url, str(downloaded_file))

            # Extract the downloaded zip to a folder with the full version number as its name
            u.extract(downloaded_file, f'jdk-{java_full_version}')
            os.rename(f'jdk-{java_full_version}', 'jdk')
            os.remove(downloaded_file)

        # macOS or Linux download
        else:
            # Download and extract AdoptOpenJDK for Mac/Linux
            download_file(f'{java_url}', 'jdk.tar.gz')
            # TODO use extract()
            os.system('gzip -d jdk.tar.gz')
            os.system('tar -xf jdk.tar')
            os.system(f'mv jdk-{java_full_version} jdk')
            os.remove('jdk.tar')

        download_complete('Java')

    download_xerces()
    download_wxwidgets()
    download_cspice()
    download_swig()
    download_java()

    print('\nDependencies download complete!')


def make_depend(dependency: str, install_type: str, debug: bool = False):
    dep_l = dependency.lower()  # convert name to lowercase
    install = 'install ' if 'install' in install_type else ''
    j_cores = f'-j{num_cores}'
    log_path = f'{logs_path}/{dep_l}_{install_type}.log'
    make_command = (f'make {install}{j_cores}'
                    # f' > "{log_path}" 2>&1'  # TODO reinstate or remove logging for make command
                    )

    try:
        if debug:
            print(f'Running "{make_command}" in "{os.getcwd()}"')
        _run_command(make_command)
        # subprocess.run(make_command.split(' '),
        #                capture_output=True,
        #                check=True, text=True, shell=True)

    except subprocess.CalledProcessError as cpe:
        print(f'Error returned by subprocess.run: "{cpe.stderr}"')
        raise RuntimeError(
            f'{dependency} {install_type} build failed. Fix errors listed in log at {log_path} and try again.')


def build_xerces():
    # # FIXME: make cross-platform
    xerces_build_path = xerces_path / 'linux-build'
    xerces_install_path = xerces_path / 'linux-install'

    if not os.path.exists(xerces_path):
        raise FileNotFoundError(f'Xerces build cannot begin because the xerces folder was not found.'
                                f'\nCurrent working directory: {os.getcwd()}')

    # Find a test file to check if xerces has already been installed
    xerces_test_file: Path = xerces_install_path / 'lib/libxerces-c.a'

    # Build xerces if the test file doesn't already exist
    if os.path.exists(xerces_test_file):
        print(f'Xerces {xerces_version} already configured')
        return

    print(f'\n********** Configuring Xerces-C++ {xerces_version} **********')

    # depends: Path = u.directories.depends
    logs_path = depends / 'logs' / 'xerces'

    # Windows-specific build
    if platform == Platform.Windows:
        xerces_outdir = f'{xerces_path}/windows-install'
        # xerces_arch = 'Win64'

        # Build Xerces if the directory doesn't already exist
        if os.path.exists(xerces_outdir):
            print('-- Xerces already configured')
            return

        os.makedirs(f'{xerces_path}/build/windows', exist_ok=True)
        os.chdir(f'{xerces_path}/build/windows')
        print('Setting up CMake...')
        os.system(
            f'cmake -G "Visual Studio {vs_major_version} {str(vs_version)}" -DBUILD_SHARED_LIBS:BOOL=OFF '
            f'-Dtranscoder=windows -DCMAKE_INSTALL_PREFIX="{xerces_outdir}" "{xerces_path}" -Wno-dev > '
            f'"{logs_path}\\xerces_cmake.log" 2>&1')

        print('-- Compiling debug Xerces. This could take a while...')
        os.system(f'cmake --build . --config Debug --target install > \
                    "{logs_path}\\xerces_build_debug.log" 2>&1')

        print('-- Compiling release Xerces. This could take a while...')
        os.system(f'cmake --build . --config Release --target install > '
                  f'"{logs_path}\\xerces_build_release.log" 2>&1')

        return

    # TODO remove old implementation
    def old() -> None:
        if platform == Platform.Windows:
            raise RuntimeError(
                'Building Xerces for Windows should have already been handled!')

        # Out-of-source xerces build/install locations
        elif platform == Platform.macOS:
            xerces_build_path = f'{xerces_path}/cocoa-build'
            xerces_install_path = f'{xerces_path}/cocoa-install'

        # Linux-specific build
        else:
            xerces_build_path = f'{xerces_path}/linux-build'
            xerces_install_path = f'{xerces_path}/linux-install'

        # Find a test file to check if xerces has already been installed
        xerces_test_file = f'{xerces_install_path}/lib/libxerces-c.a'

        # Build xerces if the test file doesn't already exist
        if os.path.exists(xerces_test_file):
            print(f'Xerces {xerces_version} already configured')
            return

        # Create build and install directories.
        os.makedirs(xerces_build_path, exist_ok=True)
        os.makedirs(xerces_install_path, exist_ok=True)

        os.chdir(xerces_build_path)  # Switch to buid directory.

        # For users who compile GMAT on multiple platforms side-by-side.
        # Running Windows configure.bat causes Mac/Linux configure scripts
        # to have missing permissions.
        os.system('chmod u+x ../configure')
        os.system('chmod u+x ../config/*')

        # Xerces needs flags on OSX
        macos_flags = '' if platform != Platform.macOS else \
            f'-mmacosx-version-min={osx_min_version} --sysroot={osx_sdk}'

        common_xerces_flags = ('--disable-shared --disable-netaccessor-curl'
                               ' --disable-transcoder-icu --disable-msgloader-icu')

        print(
            f'Configuring Xerces {xerces_version} debug library. This could take a while...')
        common_c_flags = f'-O0 -g -fPIC {macos_flags}'

        debug_configure_command = f'../configure {common_xerces_flags} CFLAGS="{common_c_flags}" CXXFLAGS="{common_c_flags}" --prefix="{xerces_install_path}" > "{logs_path}/xerces_configure_debug.log" 2>&1'
        os.system(debug_configure_command)

        make_depend('xerces', 'build_debug')
        make_depend('xerces', 'install_debug')

        os.rename(f'{xerces_install_path}/lib/libxerces-c.a',
                  f'{xerces_install_path}/lib/libxerces-cd.a')
        os.system('make clean > /dev/null 2>&1')

        print(
            f'Configuring Xerces {xerces_version} release library. This could take a while...')
        common_c_flags = f'-O2 -fPIC {macos_flags}'
        release_configure_command = f'../configure {common_xerces_flags} CFLAGS="{common_c_flags}" \
                                CXXFLAGS="{common_c_flags}" --prefix="{xerces_install_path}" \
                                > "{logs_path}/xerces_configure_release.log" 2>&1'
        os.system(release_configure_command)

        make_depend('xerces', 'build_release')
        make_depend('xerces', 'install_release')

        os.chdir('..')
        os.system(f'rm -Rf {xerces_build_path}')

    # Make build and install directories
    os.makedirs(xerces_build_path, exist_ok=True)
    os.makedirs(xerces_install_path, exist_ok=True)

    # Set and make path for logs.
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
    # FIXME fix not removing 'linux-build' folder. Believe is fixed now that gmat_path uses absolute path - to test.
    u.rm(xerces_build_path)


def build_wxwidgets():
    """
    Change directory to `wx_path`, then:

    ```console

    mkdir gtk-build
    mkdir gtk-install
    cd gtk-build
    ../configure  --enable-unicode --with-opengl --prefix="/home/will/dev/non-OH/GMAT/GMAT-src-R2025a/depends/wxWidgets/wxWidgets-3.0.4/gtk-install"
    make -j12
    make install -j12
    cd ..
    rm -rf gtk-build
    ```
    """
    print(f'\n********** Configuring wxWidgets {wx_version} **********')

    # Windows-specific build
    if platform == Platform.Windows:
        wx_path: Path = wxWidgets_path / wx_version_folder

        if not os.path.exists(wx_path):
            raise FileNotFoundError(
                wx_path, f'Could not find folder "{wx_path}" to build wxWidgets.')

        # vc141_x64_dll
        dll_folder_initial: str = f'vc{vc_major_version}{vc_minor_version}{wx_type}dll'
        dll_folder_final: str = dll_folder_initial.replace(
            wx_type, '')  # vc141dll

        if os.path.exists(f'{wx_path}/lib/{dll_folder_final}'):
            print('-- wxWidgets already configured')
            return

        os.chdir(wx_path)
        try:
            os.chdir('build/msw')
        except FileNotFoundError as e:
            e.add_note(f'\n"{e.filename}" was not found while building wxWidgets.\n\n'
                       f'\t- Current working directory: {os.getcwd()}\n'
                       f'\t- Directory contents: {os.listdir()}')
            raise e

        def wxwidgets_build_command(build_type):
            return (f'nmake -f makefile.vc OFFICIAL_BUILD=1 COMPILER_VERSION='
                    f'{vc_major_version}{vc_minor_version} {wx_tgt_cpu} SHARED=1 BUILD={build_type}'
                    f' > "{logs_path}\\wxWidgets_build_{build_type}.log" 2>&1')

        print('-- Compiling debug wxWidgets. This could take a while...')
        os.system(wxwidgets_build_command('debug'))

        print('-- Compiling release wxWidgets. This could take a while...')
        os.system(wxwidgets_build_command('release'))

        os.chdir(f'{wx_path}/lib')

        if not os.path.exists(dll_folder_final):
            os.rename(dll_folder_initial, dll_folder_final)

        # Once the build has finished, some DLLs need to be copied into gmat/application/bin and gmat/application/debug
        #  to enable the .exe to run once built. (See GMT-7534 https://gmat.atlassian.net/browse/GMT-7534)
        def copy_dlls(debug: bool = False):
            dll_source: str = f'{wx_path}/lib/{dll_folder_final}'
            dll_destination: str = f'{gmat_path}/application/{"debug" if debug else "bin"}'
            required_dlls: list[str] = [
                f'wxbase30u{"d" if debug else ""}_vc{vc_major_version}{vc_minor_version}_x64.dll',
                f'wxmsw30u{"d" if debug else ""}_core_vc{vc_major_version}{vc_minor_version}_x64.dll',
                f'wxmsw30u{"d" if debug else ""}_adv_vc{vc_major_version}{vc_minor_version}_x64.dll',
                f'wxmsw30u{"d" if debug else ""}_stc_vc{vc_major_version}{vc_minor_version}_x64.dll',
                f'wxmsw30u{"d" if debug else ""}_gl_vc{vc_major_version}{vc_minor_version}_x64.dll']

            print(f'-- Copying {"non-" if not debug else ""}debug DLLs')
            for dll in required_dlls:
                source_file: str = f'{dll_source}/{dll}'
                destination_file: str = f'{dll_destination}/{dll}'
                shutil.copyfile(source_file, destination_file)

        copy_dlls(debug=False)
        copy_dlls(debug=True)

    # macOS or Linux build
    else:
        # Set build path based on version
        wx_path: Path = wxWidgets_path / f'wxWidgets-{wx_version}'

        wx_build_path: Path = wx_path / f'{wx_platform_name}-build'
        wx_install_path: Path = wx_path / f'{wx_platform_name}-install'
        wx_test_file: Path = wx_install_path / f'lib/libwx_baseu-3.0.{wx_ext}'

        # Build wxWidgets if the test file doesn't already exist
        # Note that according to
        #   http://docs.wxwidgets.org/3.0/overview_debugging.html
        # debugging features "are always available by default", so
        # we don't build a separate debug version here.
        # IF a debug version is required in the future, then this
        # if/else block should be repeated with the --enable-debug flag
        # added to mac & linux versions of the wx ./configure command
        if os.path.exists(wx_test_file):
            print(f'wxWidgets {wx_version} already configured')
            return

        os.makedirs(wx_build_path, exist_ok=True)
        os.makedirs(wx_install_path, exist_ok=True)
        os.chdir(wx_build_path)

        print(
            f'Configuring wxWidgets {wx_version}. This could take a while...')

        macos_flags = ''
        if platform == Platform.macOS:
            # wxWidgets 3.0.2 has a compile error due to an incorrect
            # include file on OSX 10.10+. Apply patch to fix this.
            # See [GMT-5384] and http://goharsha.com/blog/compiling-wxwidgets-3-0-2-mac-os-x-yosemite/
            osx_ver = mac_plat.mac_ver()[0]
            if wx_version == '3.0.2' and osx_ver > '10.10.0':  # TODO update wx_version if it's changed globally
                os.system(
                    f'sed -i.bk "s/WebKit.h/WebKitLegacy.h/" "{wx_path}/src/osx/webview_webkit.mm"')

            # wxWidgets needs these flags on OSX
            # NOTE on liblzma: The Mac build/test machine contains liblzma (via homebrew 'xz'), which conflicts with
            #  the wxWidgets build process
            macos_flags = (f'--with-osx_cocoa --without-liblzma --with-macosx-version-min={osx_min_version} '
                           f'--with-macosx-sdk={osx_sdk}')

        prefix = Path(wx_install_path)
        if not prefix.exists():  # Check prefix directory exists
            raise FileNotFoundError(
                f'prefix directory {prefix} must exist for wxWidgets configure command.')

        wxwidgets_configure_command = (
            f'../configure {macos_flags}--enable-unicode --with-opengl --prefix="{prefix}"'
            # TODO reinstate or remove logging for wxWidgets configure command
            # f' > "{log_path}" 2>&1'
        )
        try:
            _run_command(wxwidgets_configure_command)
            # subprocess.run(wxwidgets_configure_command.split(' '),
            #                capture_output=True,
            #                check=True, text=True,
            #                shell=True)
        except subprocess.CalledProcessError as cpe:
            raise RuntimeError(cpe.stderr)

        # Compile, install, and clean wxWidgets.
        print('Making wxWidgets...')
        make_depend('wxWidgets', 'build')
        print('Installing wxWidgets...')
        # FIXME not installing into gtk-install folder like it does when running directly through terminal.
        make_depend('wxWidgets', 'install')
        os.chdir(wx_path)
        u.rm(wx_build_path)

    print('-- wxWidgets build complete!')


def build_cspice():
    print('\n********** Configuring CSPICE **********')

    def cspice_win() -> None:
        """Windows-specific build of CSPICE."""
        # Build CSPICE if cspiced.lib does not already exist
        if os.path.exists(f'{cspice_path}/{cspice_dir}/lib/cspiced.lib'):
            print('-- CSPICE already configured')
            return

        try:
            os.chdir(f'{cspice_path}/{cspice_dir}/src/cspice')

        except FileNotFoundError as e:
            e.add_note(f'\nbuild_cspice() failed to switch to {cspice_path}/windows/cspice/src/cspice.\n\n'
                       f'\t- cspice_path: {cspice_path}\n'
                       f'\t- Current working directory: {os.getcwd()}\n'
                       f'\t- Directory contents: {os.listdir()}')
            raise e

        def compile_cspice(build_type):
            print(
                f'-- Compiling {build_type} CSPICE. This could take a while...')
            os.system(f'cl /c /DEBUG /Z7 /MP -D_COMPLEX_DEFINED -DMSDOS'
                      f' -DOMIT_BLANK_CC -DNON_ANSI_STDIO -DUIOLEN_int *.c >'
                      f' "{logs_path}\\cspice_build_{build_type}.log" 2>&1')
            os.system(f'link -lib /out:..\\..\\lib\\cspiced.lib *.obj >> '
                      f'"{logs_path}\\cspice_build_{build_type}.log" 2>&1')

            os.system('del *.obj')

        compile_cspice('debug')
        compile_cspice('release')

        os.chdir(depends)

        return

    if platform == Platform.Windows:
        return cspice_win()

    # macOS or Linux build
    else:
        # Windows would have returned or thrown error so below is macOS/Linux specific
        spice_path = f'{cspice_path}/{cspice_dir}'
        tk_compile_arch = f'-m{cspice_bit}'
        os.system(f'export TKCOMPILEARCH="{tk_compile_arch}"')

        flags = '' if platform != Platform.macOS else f'-mmacosx-version-min={osx_min_version} -Wno-error=implicit-function-declaration --sysroot={osx_sdk}'

        cspice_test_file = f'{spice_path}/lib/cspiced.a'

        if os.path.exists(cspice_test_file):
            print('-- CSPICE already configured')
            return None

        os.chdir(f'{spice_path}/src/cspice')

        # Compile debug CSPICE with integer uiolen [GMT-5044]
        print('Compiling CSPICE debug library. This could take a while...')
        debug_tk_compile_options = f'{tk_compile_arch} -c -ansi {flags} -g -fPIC -DNON_UNIX_STDIO -DUIOLEN_int'
        os.environ['TKCOMPILEOPTIONS'] = debug_tk_compile_options
        make_flag = os.system(
            f'./mkprodct.csh > "{logs_path}/cspice_build_debug.log" 2>&1')

        if make_flag == 0:
            os.system('mv ../../lib/cspice.a ../../lib/cspiced.a')
        else:
            print('CSPICE debug build failed. Fix errors and try again.')

        # Compile release CSPICE with integer uiolen [GMT-5044]
        print('Compiling CSPICE release library. This could take a while...')
        release_tk_compile_options = f'{tk_compile_arch} -c -ansi {flags} -O2 -fPIC -DNON_UNIX_STDIO -DUIOLEN_int'
        os.environ['TKCOMPILEOPTIONS'] = release_tk_compile_options
        # > "{logs_path}/cspice_build_release.log" 2>&1'
        mk_product_command = f'./mkprodct.csh'
        make_flag = _run_command(mk_product_command)

        if make_flag != 0:
            raise RuntimeError(
                'CSPICE release build failed. Fix errors and try again.')

    print('-- CSPICE build complete!\n')
    return None


def build_swig():
    # Windows is pre-built
    if platform == Platform.Windows:
        print('\n-- SWIG for Windows comes pre-built')
        return

    # macOS or Linux build
    else:
        print('\n********** Configuring SWIG **********')

        # Out-of-source SWIG build/install locations
        swig_build_path = f'{swig_dir}/{swig_platform_name}-build'
        swig_install_path = f'{swig_dir}/{swig_platform_name}-install'

        # Find a test file to check if SWIG has already been installed
        swig_test_file = f'{swig_install_path}/bin/swig'

        # Build SWIG if the test file doesn't already exist
        if os.path.exists(swig_test_file):
            print(f'SWIG {swig_version} already configured')
            return

        os.makedirs(swig_build_path, exist_ok=True)
        os.chdir(swig_build_path)

        # [GMT-6892] Build static PCRE using SWIG-provided build script
        os.rename(f'../{pcre_filename}', f'./{pcre_filename}')
        os.system(
            f'../Tools/pcre-build.sh > "{logs_path}/pcre_build.log" 2>&1')

        # For users who compile GMAT on multiple platforms side-by-side.
        # Running Windows configure.bat causes Mac/Linux configure scripts
        # to have missing permissions.
        os.system('chmod u+x ../configure')

        print(
            f'Configuring SWIG {swig_version} tool. This could take a while...')
        os.system(f'../configure --prefix="{swig_install_path}" > \
                    "{logs_path}/swig_configure.log" 2>&1')

        make_depend('SWIG', 'build')
        make_depend('SWIG', 'install')

        os.chdir('..')
        os.system(f'rm -Rf {swig_build_path}')


def _run_command(command: str, log: Path | None = None) -> int:
    if log:
        with open(log, 'wb') as f:
            p = subprocess.run(command.split(' '),
                               stdout=f, stderr=f,  # check=True, text=True,
                               shell=True)
            return p.returncode

    else:
        return subprocess.run(command.split(' '),
                              capture_output=True,
                              # check=True, text=True,
                              shell=True).returncode


if __name__ == '__main__':
    print('\n*** Configuring GMAT dependencies ***\n')

    set_env_variables()

    cspice_version = 'N0067'
    # SWIG 4.2.0 is required for full Python 3.12 support as per https://gmat.atlassian.net/browse/GMT-8180
    swig_version = '4.2.0'
    pcre_version = '8.45'
    java_version = '11.0.5'
    java_update = '10'
    # GMAT before R2025a(?) uses wxWidgets 3.0.4.
    wx_version: str = '3.2.6'
    wx_version_folder: str = f'wxWidgets-{wx_version}'
    xerces_version: str = '3.2.2'
    vs_version: int = 2022
    vs_major_version: str = '17'
    vc_major_version: str = '14'
    vc_minor_version: str = '1'

    gmat_path: Path = Path(os.path.dirname(os.getcwd())
                           ).absolute()  # Path to gmat folder
    depends: Path = gmat_path / 'depends'  # Path to depends folder
    logs_path: Path = depends / 'logs'  # Path to depends/logs folder

    print(f'Configuring GMAT dependencies in "{depends}"...')

    # Create path variables
    bin_path: Path = depends / 'bin'
    f2c_path: Path = depends / 'f2c'
    cspice_path: str  # cspice_path is defined per platform below
    swig_path: Path = depends / 'swig'
    java_path: Path = depends / 'java'
    wxWidgets_path: Path = depends / 'wxWidgets'
    xerces_path: Path = depends / 'xerces'
    sofa_path: Path = depends / 'sofa'
    tsplot_path: Path = depends / 'tsPlot'

    # Create log directory
    if not os.path.exists(logs_path):
        os.mkdir(logs_path)

    # Platform-based setup
    swig_dir = f'{swig_path}/swig'
    match sys.platform:
        case 'win32':
            platform: Platform = Platform.Windows
            PLATFORM_NAME = 'windows'
            # noinspection PyRedeclaration
            swig_dir = f'{swig_path}/swigwin'
            swig_platform_name = 'windows'
            setup_windows()

        case 'darwin':
            platform: Platform = Platform.macOS
            PLATFORM_NAME = 'macosx'

            cmake_platform_name = 'cocoa'
            wx_platform_name = 'cocoa'
            swig_platform_name = 'cocoa'

            wx_ext = 'dylib'

        case _:
            platform: Platform = Platform.Linux
            PLATFORM_NAME = 'linux'
            cmake_platform_name = 'linux'
            wx_platform_name = 'gtk'
            swig_platform_name = 'linux'
            wx_ext = 'so'

    cspice_path = f'{depends}/cspice/{PLATFORM_NAME}'

    java_path = Path(f'{java_path}/{PLATFORM_NAME}')

    if struct.calcsize("P") * 8 == 32:
        # TODO Fill with any lines that ask about CPU bit-ness
        wx_type = '_'
        wx_tgt_cpu = ''
        cspice_bit = '32'
    else:  # assume 64-bit
        wx_type = '_x64_'
        wx_tgt_cpu = 'TARGET_CPU=X64'
        cspice_bit = '64'

    # Set up dir/file names for downloaded files
    cspice_dir = f'cspice{cspice_bit}'
    pcre_filename = f'pcre-{pcre_version}.tar.gz'

    # Get number of cores for multithreaded compilation
    num_cores = str(os.cpu_count())
    if num_cores == 'None':
        num_cores = '1'

    download_depends()  # download GMAT dependencies (Xerces, wxWidgets, CSPICE, SWIG)

    # Build the dependencies using CMake
    build_xerces()
    build_wxwidgets()
    build_cspice()
    build_swig()

    print('\n*** Done configuring GMAT dependencies ***\n')
