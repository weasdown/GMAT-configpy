# Version of configure.py that supports specifying build parameters as command line arguments
import sys
import os
import struct
import shutil
import tarfile
import platform as mac_plat

# Example prototype command: python config-cmdline.py configs=1

...  # cmd package example
# import cmd


# class HelloWorld(cmd.Cmd):
#     """Simple command processor example."""
#
#     intro = 'Welcome to the GMAT compilation configurator. Type help or ? to list commands.\n'
#     prompt = '(GMAT config) '
#
#     @staticmethod
#     def do_greet(line):
#         """
#         Be greeted.
#
#         line: str
#         """
#         print(f'Hello! Here\'s your text: {str(line)}')
#
#     @staticmethod
#     def do_EOF():
#         return True
#
#
# if __name__ == '__main__':
#     HelloWorld().cmdloop()

gmat_path = os.path.dirname(os.path.abspath(os.getcwd()))  # Path to gmat folder (cwd is in GMAT/depends)
depends_dir = str(f'{gmat_path}/depends')  # Path to depends folder
app_debug_dir = f'{gmat_path}/application/debug'  # Path to folder for wxWidgets debug files
logs_path = f'{depends_dir}/logs'  # Path to depends/logs folder
bin_path = f'{depends_dir}/bin'

# Create path variables
depends_paths = {
    'f2c': f'{depends_dir}/f2c',
    'cspice': f'{depends_dir}/cspice',
    'swig': f'{depends_dir}/swig',
    'java': f'{depends_dir}/java',
    'wxWidgets': f'{depends_dir}/wxWidgets',
    'xerces': f'{depends_dir}/xerces',
    'sofa': f'{depends_dir}/sofa',
    'tsplot': f'{depends_dir}/tsPlot',
}

# Store dependency versions
versions = {
    'cspice': 'N0067',
    'swig': '4.0.2',
    'pcre': '8.45',
    'java': '11.0.5',
    'java_update': '10',
    'wxWidgets': '3.0.4',
    'xerces': '3.2.2',
    'osx_min': '10.15',
    'osx_sdk': '/Library/Developer/CommandLineTools/SDKs/MacOSX10.15.sdk',
    'vs': 2022,
    'vs_major': '17',
    'vc_major': '14',
    'vc_minor': '1',
}
osx_min_version = versions['osx_min']
osx_sdk = versions['osx_sdk']


def setup_windows():
    vs_arch = 'x86' if bits_32 else 'x86_amd64'  # TODO 64-bit; change to x86 for 32-bit

    vc_major_version = versions['vc_major']
    vs_version = versions['vs']

    vs_tools = f'vs{vc_major_version}0comntools'
    if vs_version >= 2017:
        vs_path_base: str = f'{os.getenv("ProgramFiles")}/Microsoft Visual Studio/{vs_version}'

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
            sys.exit("Could not find suitable Visual Studio development environment.")

        syscall: str = f'{vs_path}/../../VC/Auxiliary/Build/vcvarsall.bat'

    elif vs_version <= 2015:
        vs_path = os.getenv(vs_tools)
        syscall = f'{vs_path}/../../VC/vcvarsall.bat'

    else:
        raise ValueError(f'Visual Studio version not recognised - {vs_version}.')

    vs_env_command = f'"{syscall}" {vs_arch} & set > vsEnvironment.txt'
    print(f'Running {vs_env_command}')
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

    print("\nWindows setup complete\n")


def download_depends(params: dict):
    """
    Download GMAT dependencies.
    """

    def download_xerces():
        xerces_path = depends_paths['xerces']

        # Download xerces if it doesn't already exist
        if os.path.exists(xerces_path):
            print('-- Xerces already downloaded')
            return

        os.chdir(depends_dir)

        # Download and extract xerces
        version = versions['xerces']
        print(f'\nDownloading Xerces-C {version}...')
        xerces_dl_com = (f'curl -L http://archive.apache.org/dist/xerces/c/3/sources/xerces-c-{version}.tar.gz'
                         f' > xerces.tar.gz')
        os.system(xerces_dl_com)  # run the Xerces download command
        with tarfile.open('xerces.tar.gz', 'r:gz') as tar:
            tar.extractall()
        os.remove('xerces.tar.gz')

        # Rename the extracted xerces directory to be the proper path
        xerces_version_folder = f'xerces-c-{version}'
        xerces_folder_simple = os.path.basename(os.path.normpath(xerces_path))
        os.rename(xerces_version_folder, xerces_folder_simple)

    def download_wxwidgets():
        # Download wxWidgets if it doesn't already exist
        wxwidgets_path = depends_paths['wxWidgets']
        version = versions['wxWidgets']

        # Download wxWidgets if it doesn't already exist
        if os.path.exists(wxwidgets_path):
            print('-- wxWidgets already downloaded')
            return

        if not os.path.exists(f'{wxwidgets_path}/wxWidgets-{version}'):
            # Create & change directories
            if not os.path.exists(wxwidgets_path):
                os.mkdir(wxwidgets_path)
            os.chdir(wxwidgets_path)

            # Download wxWidgets source
            print(f'\nDownloading wxWidgets {version}...')
            os.system(f'curl -L https://github.com/wxWidgets/wxWidgets/releases/download/'
                      f'v{version}/wxWidgets-{version}.tar.bz2 > wxWidgets.tar.bz2')
            with tarfile.open('wxWidgets.tar.bz2', 'r:bz2') as tar:
                tar.extractall()
            os.remove('wxWidgets.tar.bz2')

            # Make sure wxWidgets was downloaded
            if not os.path.exists(f'{wxwidgets_path}/wxWidgets-{version}'):
                raise RuntimeError(f'Error in wxWidgets-{version} download.')

    def download_cspice(opts: dict):
        # Download CSPICE if it doesn't already exist
        cspice_path = opts['path']
        version = versions['cspice']
        direc = opts['dir']

        if os.path.exists(cspice_path):
            print('-- CSPICE already downloaded')
            return

        # Create & change directories
        os.makedirs(cspice_path, exist_ok=True)
        os.chdir(cspice_path)

        print(f'\nDownloading {cpu_bits}-bit CSPICE {version}...')
        if windows:
            # Download and extract Spice for Windows (32/64-bit)
            if os.path.exists(f'{cspice_path}/{direc}'):
                print('CSPICE already downloaded')
                return
            zip_name = f'{direc}.zip'
            cspice_dl_com = (f'curl -L https://naif.jpl.nasa.gov/pub/naif/toolkit//C/PC_Windows_VisualC_'
                             f'{cpu_bits}bit/packages/cspice.zip > {zip_name}')
            os.system(cspice_dl_com)  # run command to download CSPICE
            os.system(f'"{depends_dir}/bin/7za/7za.exe" x {zip_name} > nul')
            # os.system(f'"{depends_dir}/bin/7za/7za.exe" x cspice.zip > cspice')  # TODO remove
            # os.chdir(cspice_path)  # cspice_path: depends/cspice for now
            os.rename('cspice', direc)
            os.remove(zip_name)

        else:  # Platform is not Windows
            # Download and extract Spice for Mac/Linux (32/64-bit)
            cspice_type = opts['type']
            os.system(f'curl https://naif.jpl.nasa.gov/pub/naif/misc/toolkit_"{version}"/C/'
                      f'{cspice_type}"_{cpu_bits}/packages/cspice.tar.Z > cspice.tar.Z')
            os.system('gzip -d cspice.tar.Z')
            os.system('tar -xf cspice.tar')
            os.system(f'mv cspice {direc}')
            os.remove('cspice.tar')

    def download_swig(opts: dict):
        # Download SWIG if it doesn't already exist
        swig_direc = opts['dir']
        swig_path = depends_paths['swig']
        version = versions['swig']

        # Check platform-appropriate path
        if os.path.exists(swig_direc):
            print('-- SWIG already downloaded')
            return

        # Create & change directories
        os.chdir(depends_dir)
        os.makedirs(f'{depends_dir}/swig', exist_ok=True)
        os.makedirs(swig_path, exist_ok=True)  # Duplication?
        os.chdir(swig_path)

        print(f'\nDownloading SWIG {version}...')

        if windows:
            # Download and extract SWIG for Windows
            os.system(f'curl -L http://download.sourceforge.net/swig/swigwin-{version}.zip > swig.zip')
            os.system(f'"{depends_dir}/bin/7za/7za.exe" x swig.zip > nul')
            os.rename(f'swigwin-{version}', 'swigwin')
            os.remove('swig.zip')
        else:
            # Download and extract SWIG for Mac/Linux
            os.system(f'curl -L http://download.sourceforge.net/swig/swig-{version}.tar.gz > swig.tar.gz')
            os.system('gzip -d swig.tar.gz')
            os.system('tar -xf swig.tar')
            os.system(f'mv swig-{version} swig')
            os.remove('swig.tar')

            # [GMT-6892] Download PCRE into SWIG directory
            pcre_version = versions['pcre']
            pcre_name = opts['pcre_name']
            print(f'\nDownloading PCRE {pcre_version} for use with SWIG...')
            os.chdir(swig_direc)
            os.system(f'curl -L https://sourceforge.net/projects/pcre/files/pcre/'
                      f'{pcre_version}/{pcre_name}/download > {pcre_name}')

    def download_java(opts: dict):
        # Download Java if it doesn't already exist
        java_path = depends_paths['java']
        version = versions['java']
        update = versions['java_update']

        if os.path.exists(java_path):
            print('-- Java already downloaded')
            return

        # Create & change directories
        os.makedirs(java_path, exist_ok=True)
        os.chdir(java_path)

        java_major_version = version.split('.')[0]
        java_full_version = f'{version}+{update}'

        java_base_url = (f'https://github.com/AdoptOpenJDK/openjdk{java_major_version}'
                         f'-binaries/releases/download/jdk-{java_full_version}/')
        java_url = (f'{java_base_url}OpenJDK{java_major_version}U-jdk_x64_{opts["plat"]}'
                    f'_hotspot_{version}_{update}')

        print(f'\nDownloading Java JDK {java_full_version}...')
        if windows:
            # Download and extract AdoptOpenJDK for Windows
            # print(f"curl command for Java download: curl -L '{java_url}.zip'")  # my code
            os.system(f'curl -L {java_url}.zip > jdk.zip')
            os.system(f'"{depends_dir}/bin/7za/7za.exe" x jdk.zip > nul')
            os.rename(f'jdk-{java_full_version}', 'jdk')
            os.remove('jdk.zip')
        else:
            # Download and extract AdoptOpenJDK for Mac/Linux
            os.system(f'curl -L {java_url}.tar.gz > jdk.tar.gz')
            os.system('gzip -d jdk.tar.gz')
            os.system('tar -xf jdk.tar')
            os.system(f'mv jdk-{java_full_version} jdk')
            os.remove('jdk.tar')

    print('\n*** Downloading GMAT dependencies ***')

    download_xerces()
    download_wxwidgets()
    download_cspice(params['cspice_opts'])
    download_swig(params['swig_opts'])
    download_java(params['java_opts'])

    print("\nDependencies download complete")


def make_depend(dependency: str, install_type: str):
    dep_l = dependency.lower()  # convert name to lowercase
    install = 'install ' if install_type == 'install' else ''
    j_cores = f' -j{cores}' if 'build' in install_type else ''
    make_flag = os.system(f'make {install}{j_cores}> "{logs_path}/{dep_l}_{install_type}.log" 2>&1')
    if make_flag != 0:
        raise RuntimeError(f'{dependency} {install_type} build failed. Fix errors and try again.')


def build_xerces(debug: bool, release: bool, ):
    xerces_path = depends_paths['xerces']
    version = versions['xerces']

    if not os.path.exists(xerces_path):
        raise FileNotFoundError(f'Xerces build cannot begin because the xerces folder was not found.'
                                f'\nCurrent working directory: {os.getcwd()}')

    print(f'\n********** Configuring Xerces-C++ {version} **********')

    # Windows-specific build
    if windows:
        xerces_outdir = f'{xerces_path}/windows-install'
        # xerces_arch = 'Win64'

        # Build Xerces if the directory doesn't already exist
        if os.path.exists(xerces_outdir):
            print('-- Xerces already configured')
            return

        os.makedirs(f'{xerces_path}/build/windows', exist_ok=True)
        os.chdir(f'{xerces_path}/build/windows')
        print('-- Setting up Xerces build')
        vs_maj_ver = versions['vs_major']
        vs_ver = versions['vs']
        arch = 'Win64'  # TODO: dependent on 32/64-bit?

        # From clean configure.py: (TODO remove - debugging only)
        # os.system('cmake -G "Visual Studio ' + vs_major_version + ' ' + str(vs_version) + ' ' + xerces_arch +
        #           '" -DBUILD_SHARED_LIBS:BOOL=OFF -Dtranscoder=windows -DCMAKE_INSTALL_PREFIX="' + xerces_outdir +
        #           '" "' + xerces_path + '"  > ' + logs_path + '\\xerces_cmake.log 2>&1')

        os.system(
            f'cmake -G "Visual Studio {vs_maj_ver} {vs_ver}" -DBUILD_SHARED_LIBS:BOOL=OFF -Dtranscoder=windows '
            f'-DCMAKE_INSTALL_PREFIX="{xerces_outdir}" "{xerces_path}" > "{logs_path}/xerces_cmake.log" 2>&1')

        if debug:
            print('-- Compiling debug Xerces. This could take a while...')
            os.system(f'cmake --build . --config Debug --target install > "{logs_path}/xerces_build_debug.log" 2>&1')

        if release:
            print('-- Compiling release Xerces. This could take a while...')
            os.system(f'cmake --build . --config Release --target install > '
                      f'"{logs_path}/xerces_build_release.log" 2>&1')

        return

    # Out-of-source xerces build/install locations
    elif macos:
        xerces_build_path = f'{xerces_path}/cocoa-build'
        xerces_install_path = f'{xerces_path}/cocoa-install'
    else:
        xerces_build_path = f'{xerces_path}/linux-build'
        xerces_install_path = f'{xerces_path}/linux-install'

    # Find a test file to check if xerces has already been installed
    xerces_test_file = f'{xerces_install_path}/lib/libxerces-c.a'

    # Build xerces if the test file doesn't already exist
    if os.path.exists(xerces_test_file):
        print(f'Xerces {version} already configured')
        return

    os.mkdir(xerces_build_path)
    os.chdir(xerces_build_path)

    # For users who compile GMAT on multiple platforms side-by-side.
    # Running Windows configure.bat causes Mac/Linux configure scripts
    # to have missing permissions.
    os.system('chmod u+x ../configure')
    os.system('chmod u+x ../config/*')

    # Xerces needs flags on OSX
    macos_flags = '' if sys.platform != 'darwin' else f'-mmacosx-version-min={osx_min_version} --sysroot={osx_sdk}'

    common_xerces_flags = ('--disable-shared --disable-netaccessor-curl'
                           ' --disable-transcoder-icu --disable-msgloader-icu')

    if debug:
        print(f'Configuring Xerces {version} debug library. This could take a while...')
        common_c_flags = f'-O0 -g -fPIC {macos_flags}'
        os.system(f'../configure {common_xerces_flags} CFLAGS="{common_c_flags}" CXXFLAGS={common_c_flags}" '
                  f'--prefix="{xerces_install_path}" > {logs_path}/xerces_configure_debug.log" 2>&1')

        make_depend('xerces', 'build_debug')
        make_depend('xerces', 'install_debug')

        os.rename(f'{xerces_install_path}/lib/libxerces-c.a',
                  f'{xerces_install_path}/lib/libxerces-cd.a')
        os.system('make clean > /dev/null 2>&1')

    if release:
        print(f'Configuring Xerces {version} release library. This could take a while...')
        common_c_flags = f'-O2 -fPIC {macos_flags}'
        os.system(f'../configure {common_xerces_flags} CFLAGS="{common_c_flags}" CXXFLAGS="{common_c_flags}" '
                  f'--prefix="{xerces_install_path}" > "{logs_path}/xerces_configure_release.log" 2>&1')

        make_depend('xerces', 'build_release')
        make_depend('xerces', 'install_release')

    os.chdir('..')
    os.system(f'rm -Rf {xerces_build_path}')


def build_wxWidgets(debug: bool, release: bool, opts: dict[str, str]):
    version = versions['wxWidgets']
    print(f'\n********** Configuring wxWidgets {version} **********')

    wx_type: str = opts.get('type', None)
    target_cpu: str = opts['cpu']
    wxwidgets_path = depends_paths['wxWidgets']

    # Windows-specific build
    if windows:
        # Generate filenames to download
        wx_path = f'wxWidgets/wxWidgets-{version}'
        os.chdir(depends_dir)  # switch back to depends so later relative directory changes work

        # Download wxWidgets files if they don't already exist
        if os.path.exists(f'{wx_path}/lib/vc{wx_type}dll'):
            print('-- wxWidgets already configured')
            return

        os.makedirs(wx_path, exist_ok=True)
        os.chdir(wx_path)
        try:
            os.chdir('build/msw')
        except FileNotFoundError:
            print(f'Current directory: {os.getcwd()}')
            print(f'Items in directory: {os.listdir()}')
            raise

        vc_major_version = versions['vc_major']
        vc_minor_version = versions['vc_minor']

        def wxwidgets_build_command(build_type):
            return (f'nmake -f makefile.vc OFFICIAL_BUILD=1 COMPILER_VERSION='
                    f'{vc_major_version}{vc_minor_version} {target_cpu} SHARED=1 BUILD={build_type}'
                    f' > "{logs_path}/wxWidgets_build_{build_type}.log" 2>&1')

        if debug:
            print('-- Compiling debug wxWidgets. This could take a while...')
            os.system(wxwidgets_build_command('debug'))

        if release:
            print('-- Compiling release wxWidgets. This could take a while...')
            os.system(wxwidgets_build_command('release'))

        os.chdir('../..')

        os.chdir('lib')
        os.rename(f'vc{vc_major_version}{vc_minor_version}{wx_type}dll', f'vc{wx_type}dll')  # rename folder

        os.chdir(depends_dir)

        # Once the build has finished, full contents (TODO) of vc_x64_dll folder need to be copied into gmat/application/debug
        #  to enable Windows debug build. (See GMT-7534 https://gmat.atlassian.net/browse/GMT-7534)
        if debug:
            wx_db_source = f'{wxwidgets_path}/wxWidgets-{version}/lib/vc_x64_dll'
            files = os.listdir(wx_db_source)
            files = os.listdir(wx_db_source)
            for file in files:
                shutil.copytree(wx_db_source, app_debug_dir, dirs_exist_ok=True)

    else:  # running on something other than Windows
        # Set build path based on version
        wx_path = f'{wxwidgets_path}/wxWidgets-{version}'

        wx_build_path = f'{wx_path}/{plat}-build'
        wx_install_path = f'{wx_path}/{plat}-install'
        ext = opts['ext']
        wx_test_file = f'{wx_install_path}/lib/libwx_baseu-3.0.{ext}'

        # Build wxWidgets if the test file doesn't already exist
        # Note that according to
        #   http://docs.wxwidgets.org/3.0/overview_debugging.html
        # debugging features "are always available by default", so
        # we don't build a separate debug version here.
        # IF a debug version is required in the future, then this
        # if/else block should be repeated with the --enable-debug flag
        # added to mac & linux versions of the wx ./configure command
        if os.path.exists(wx_test_file):
            print(f'wxWidgets {version} already configured')
            return

        os.makedirs(wx_build_path, exist_ok=True)
        os.chdir(wx_build_path)

        print(f'Configuring wxWidgets {version}. This could take a while...')

        macos_flags = ''
        if macos:
            # wxWidgets 3.0.2 has a compile error due to an incorrect
            # include file on OSX 10.10+. Apply patch to fix this.
            # See [GMT-5384] and http://goharsha.com/blog/compiling-wxwidgets-3-0-2-mac-os-x-yosemite/
            osx_ver = mac_plat.mac_ver()[0]
            if version == '3.0.2' and osx_ver > '10.10.0':
                os.system(f'sed -i.bk "s/WebKit.h/WebKitLegacy.h/" "{wx_path}/src/osx/webview_webkit.mm"')

            # wxWidgets needs these flags on OSX
            # NOTE on liblzma: The Mac build/test machine contains liblzma (via homebrew 'xz'), which conflicts with
            #  the wxWidgets build process
            macos_flags = (f'--with-osx_cocoa --without-liblzma --with-macosx-version-min={osx_min_version} '
                           f'--with-macosx-sdk={osx_sdk}')

        os.system(f'../configure {macos_flags} --enable-unicode --with-opengl --prefix="{wx_install_path}" '
                  f'> "{logs_path}/wxWidgets_configure.log" 2>&1')

        # Compile, install, and clean wxWidgets
        make_depend('wxWidgets', 'build')
        make_depend('wxWidgets', 'install')
        os.chdir('..')
        os.system(f'rm -Rf "{wx_build_path}"')


def build_cspice(debug: bool, release: bool, opts: dict):
    print('\n********** Configuring CSPICE **********')
    path = opts['path']
    direc = opts['dir']

    if windows:
        # # Build CSPICE if cspiced.lib does not already exist
        # if debug and os.path.exists(f'{path}/{direc}/lib/cspiced.lib') or os.path.exists(f'{path}/{direc}/lib/cspice.lib'):
        #     # TODO separate conditions for release/debug and build a missing one even if other present
        #     print('-- CSPICE already configured')
        #     return

        try:
            os.chdir(f'{path}/{direc}/src/cspice')
        except FileNotFoundError:
            print(f'build_cspice: Failed to switch to {path}/windows/cspice/src/cspice')
            print(f'cspice_path: {path}')
            print(f'Current working directory: {os.getcwd()}')
            print(f'Directory contents: {os.listdir()}')
            raise

        def compile_cspice(build_type: str):
            # From clean configure.py: (TODO remove - debugging only)
            # os.system('cl /c /DEBUG /Z7 /MP -D_COMPLEX_DEFINED -DMSDOS'
            #           ' -DOMIT_BLANK_CC -DNON_ANSI_STDIO -DUIOLEN_int *.c >'
            #           ' ' + logs_path + '/cspice_build_debug.log 2>&1')
            # os.system('link -lib /out:../../lib/cspiced.lib *.obj >> ' + logs_path + '/cspice_build_debug.log 2>&1')

            # os.system('del *.obj')

            # print('-- Compiling release CSPICE. This could take a while...')
            # os.system('cl /c /O2 /MP -D_COMPLEX_DEFINED -DMSDOS'
            #           ' -DOMIT_BLANK_CC -DNON_ANSI_STDIO -DUIOLEN_int *.c >'
            #           ' ' + logs_path + '/cspice_build_release.log 2>&1')
            # os.system('link -lib /out:../../lib/cspice.lib *.obj >> ' + logs_path + '/cspice_build_release.log 2>&1')

            # os.system('del *.obj')

            # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

            if build_type == 'debug':
                build_flag = '/DEBUG /Z7'
                lib_flag = 'd'
            elif build_type == 'release':
                build_flag = '/O2'
                lib_flag = ''
            else:
                raise SyntaxError(f'build_type "{build_type}" not recognized')

            os.chdir(f'{path}/{direc}/src/cspice')
            print(os.getcwd())
            print(f'-- Compiling {build_type} CSPICE. This could take a while...')
            os.system(f'cl /c {build_flag} /MP -D_COMPLEX_DEFINED -DMSDOS'
                      f' -DOMIT_BLANK_CC -DNON_ANSI_STDIO -DUIOLEN_int *.c >'
                      f' "{logs_path}/cspice_build_{build_type}.log" 2>&1')
            os.system(f'link -lib /out:../../lib/cspice{lib_flag}.lib *.obj >> '
                      f'"{logs_path}/cspice_build_{build_type}.log" 2>&1')

            os.system('del *.obj')

        if debug:
            compile_cspice('debug')
        if release:
            compile_cspice('release')

        os.chdir(depends_dir)
        return

    else:
        # macOS/Linux specific
        spice_path = f'{path}/{direc}'
        tk_compile_arch = f'-m{cpu_bits}'
        os.system(f'export TKCOMPILEARCH="{tk_compile_arch}"')

        flags = '' if sys.platform != 'darwin' else (f'-mmacosx-version-min={osx_min_version} '
                                                     f'-Wno-error=implicit-function-declaration --sysroot={osx_sdk}')

        cspice_test_file = f'{spice_path}/lib/cspiced.a'

        if os.path.exists(cspice_test_file):
            print('-- CSPICE already configured')
        else:
            os.chdir(f'{spice_path}/src/cspice')

        if debug:
            # Compile debug CSPICE with integer uiolen [GMT-5044]
            print('Compiling CSPICE debug library. This could take a while...')
            os.environ[
                'TKCOMPILEOPTIONS'] = f'{tk_compile_arch} -c -ansi {flags} -g -fPIC -DNON_UNIX_STDIO -DUIOLEN_int'
            make_flag = os.system(f'./mkprodct.csh > "{logs_path}/cspice_build_debug.log" 2>&1')

            if make_flag == 0:
                os.system('mv ../../lib/cspice.a ../../lib/cspiced.a')
            else:
                print('CSPICE debug build failed. Fix errors and try again.')

        if release:
            # Compile release CSPICE with integer uiolen [GMT-5044]
            print('Compiling CSPICE release library. This could take a while...')
            os.environ[
                'TKCOMPILEOPTIONS'] = f'{tk_compile_arch} -c -ansi {flags} -O2 -fPIC -DNON_UNIX_STDIO -DUIOLEN_int'
            make_flag = os.system(f'./mkprodct.csh > "{logs_path}/cspice_build_release.log" 2>&1')

            if make_flag != 0:
                print('CSPICE release build failed. Fix errors and try again.')


def build_swig(opts: dict):
    # Windows is pre-built
    if windows:
        print('\n-- SWIG for Windows comes pre-built')
        return

    print('\n********** Configuring SWIG **********')
    direc = opts['dir']
    swig_build_path = f'{direc}/{plat}-build'
    swig_install_path = f'{direc}/{plat}-install'

    # Find a test file to check if SWIG has already been installed
    swig_test_file = f'{swig_install_path}/bin/swig'

    version = versions['swig']

    # Build SWIG if the test file doesn't already exist
    if os.path.exists(swig_test_file):
        print(f'SWIG {version} already configured')
        return

    os.makedirs(swig_build_path, exist_ok=True)
    os.chdir(swig_build_path)

    # [GMT-6892] Build static PCRE using SWIG-provided build script
    pcre_name = opts['pcre_name']
    os.rename(f'../{pcre_name}', f'./{pcre_name}')
    os.system(f'../Tools/pcre-build.sh > "{logs_path}/pcre_build.log" 2>&1')

    # For users who compile GMAT on multiple platforms side-by-side.
    # Running Windows configure.bat causes Mac/Linux configure scripts
    # to have missing permissions.
    os.system('chmod u+x ../configure')

    print(f'Configuring SWIG {version} tool. This could take a while...')
    os.system(f'../configure --prefix="{swig_install_path}" > "{logs_path}/swig_configure.log" 2>&1')

    make_depend('SWIG', 'build')
    make_depend('SWIG', 'install')

    os.chdir('..')
    os.system(f'rm -Rf {swig_build_path}')


def prompt(allowed_values: dict, prompt_text: str, print_selection: bool = False):
    def options_bullets(options: dict) -> str:
        output: str = ''
        for item in list(options.items())[1:]:
            output += f'\n\t{item[0]}: {item[1]}'
        return output

    default = allowed_values.get('default')
    if default is None:
        raise AttributeError(f'default value must be explicitly specified in options dict. '
                             f'Supplied dict: {allowed_values}')
    try:
        val: str = input(f'\nPlease select {prompt_text} [{default}]:{options_bullets(allowed_values)}\n')
        selection = default if val == '' else int(val)
        selected = str(allowed_values.get(selection, None))
        if selected is None:
            print('Please choose a valid option')
            prompt(allowed_values, prompt_text)
        else:
            if print_selection:
                print(f'\nSelected option: {selected}')
        return selection, selected

    except ValueError:
        print('Selection must be specified as an integer')
        prompt(allowed_values, prompt_text)


def py_ver_prompt():
    default = 'All'
    major_ver = 3
    minor_ver_min = 6
    minor_ver_max = 12
    min_ver = f'{major_ver}.{minor_ver_min}'
    max_ver = f'{major_ver}.{minor_ver_max}'
    vers = input('Please specify which version(s) of Python to build for, separating with commas '
                 'for multiple versions. You can also specify "All" to build all allowed versions '
                 f'({min_ver}-{max_ver}) [All]\n')

    if vers == '':  # use default option - All versions
        vers = ','.join([f'{major_ver}.{minor}' for minor in range(minor_ver_min, minor_ver_max + 1)])
    else:
        vers = str(vers)

    # Check that all specified versions are valid
    vers = vers.split(',')
    for ver in vers:
        ver = ver.replace(' ', '')  # remove any spaces
        major, minor = ver.split('.')  # split into major and minor parts of version number
        if (int(major) != 3) or (int(minor) < minor_ver_min) or (int(minor) > minor_ver_max):
            raise ValueError(f'Invalid Python version specified: {ver}')

    return vers


def setup():
    # Platform-based setup
    print('\n*** Running initial setup ***\n')

    # Create log directory
    if not os.path.exists(logs_path):
        os.mkdir(logs_path)

    cpu_cores: int = os.cpu_count() if os.cpu_count() is not None else 1  # num cores for multithreaded compilation

    pcre_params = {'pcre_ver': versions['pcre'],
                   'pcre_name': f'pcre-{versions["pcre"]}.tar.gz', }
    wx_bit_dependent = {'type': '_', 'cpu': ''} if bits_32 else {'type': '_x64_', 'cpu': 'TARGET_CPU=X64'}
    platform_specific: dict[str, dict] = {
        'win32': {  # Windows
            'wx_opts': {'plat': plat},
            # 'cmake_plat': 'windows',  # TODO required? Correct?
            'cspice_plat': 'windows',
            'java_plat': 'windows',
            'swig_opts': {'plat': 'windows', 'dir': f'{depends_paths["swig"]}/swigwin'},
        },
        'darwin': {  # macOS
            'wx_opts': {'plat': 'cocoa', 'ext': 'dylib'},
            'cspice_plat': 'macosx',
            # 'cmake_plat': 'cocoa',
            'java_plat': 'macosx',
            'swig_opts': {'plat': 'cocoa', 'dir': f"{depends_paths['swig']}/swig"} | pcre_params,
        },
        'linux': {  # Linux
            'wx_opts': {'plat': 'gtk', 'ext': 'so'},
            'cspice_plat': 'linux',
            # 'cmake_plat': 'linux',
            'java_plat': 'linux',
            'swig_opts': {'plat': 'linux', 'dir': f"{depends_paths['swig']}/swig"} | pcre_params,
        }
    }

    def java_opts(platform: str) -> dict[str, str]:
        java_plat = platform_specific.get(platform).get('java_plat')

        return {'plat': java_plat,
                'path': f'{depends_paths["java"]}/{java_plat}'}

    sys_params: dict = {
        'sys_plat': plat,
        'cores': cpu_cores,
        'bits': cpu_bits,

        'cspice_opts': {'path': f'{depends_paths["cspice"]}/{platform_specific.get(plat).get("cspice_plat")}',
                        'dir': f'cspice{cpu_bits}',  # TODO remove
                        # 'dir': 'cspice',  # TODO remove
                        'type': 'MacIntel_OSX_AppleC' if macos else 'PC_Linux_GCC',
                        },
        'java_opts': java_opts(plat),
    }
    sys_params.update(platform_specific.get(plat))  # add platform-specific params to sys_params
    sys_params['wx_opts'].update(wx_bit_dependent)  # apply bit-dependent wxWidgets params

    return sys_params


def menu():
    print('*** GMAT compilation configuration wizard ***')
    config_values = {'default': 1, 1: 'release only', 2: 'debug only', 3: 'debug and release'}
    api_values = {'default': 1, 1: 'None', 2: 'Python only', 3: 'Java only', 4: 'Python and Java'}

    config, config_desc = prompt(config_values, 'a build configuration')
    debug = True if 'debug' in config_desc else False
    release = True if 'release' in config_desc else False

    api, api_desc = prompt(api_values, 'which API(s) to build')

    if 'Python' in api_desc:
        py_versions = py_ver_prompt()

        if debug:
            # check Python debug libs
            print('Specified options include debug configuration and Python API. Checking Python debug libs...')
            platform = sys.platform
            if platform != 'win32':
                print('Current platform is not Windows so no problem.')
                return True
            else:
                appdata_local = os.getenv('LOCALAPPDATA')
                for ver in py_versions:
                    ver_num = ver.replace('.', '')
                    py_root = f'{appdata_local}/Programs/Python/Python{ver_num}/libs'
                    debug_lib = f'python{ver_num}_d.lib'
                    if not os.path.isfile(f'{py_root}/{debug_lib}'):
                        raise FileNotFoundError(f'Could not find debug lib for Python {ver}')
                    else:
                        print(f'\t- Found debug lib for Python {ver}')

    if 'Java' in api_desc:
        raise NotImplementedError

    print(f'Setting up configuration "{config_desc}" '
          f'{f"with APIs {api_desc}" if api_desc != "None" else "without APIs"}')

    return debug, release


windows = macos = linux = False  # current platform will be set to true in setup()
plat = sys.platform  # platform that this file is running on
if plat == 'win32':
    windows = True
elif plat == 'darwin':
    macos = True
else:
    linux = True

cpu_bits: int = struct.calcsize('P') * 8  # number of CPU bits (32-bit or 64-bit)
bits_32: bool = True if cpu_bits == 32 else False

setup_params: dict = setup()
cores = setup_params['cores']

db, rl = menu()  # debug and release bools

if windows:
    setup_windows()

download_depends(setup_params)

# def build_depends():
build_cspice(db, rl, setup_params['cspice_opts'])
build_xerces(db, rl)
wx_opts = setup_params['wx_opts']
build_wxWidgets(db, rl, setup_params['wx_opts'])
build_swig(setup_params['swig_opts'])
