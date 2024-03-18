import os
import sys
import tarfile
import struct
import platform as mac_plat
import shutil


# Load the Visual Studio path settings
def setup_windows():
    # 64-bit; change to x86 for 32-bit
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
            sys.exit("Could not find suitable Visual Studio development environment.")

        syscall: str = f'{vs_path}/../../VC/Auxiliary/Build/vcvarsall.bat'

    elif vs_version <= 2015:
        vs_path = os.getenv(vs_tools)
        syscall = f'{vs_path}/../../VC/vcvarsall.bat'

    else:
        raise ValueError(f'Visual Studio version not recognised - {vs_version}.')

    vs_env_command = f'\"{syscall}\" {vs_arch} & set > vsEnvironment.txt'
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


def download_depends():
    """
    Download GMAT dependencies.
    """

    def download_xerces():
        # Download xerces if it doesn't already exist
        if os.path.exists(xerces_path):
            print('Xerces already downloaded')
            return

        os.chdir(depends_path)

        # Download and extract xerces
        print(f'\nDownloading Xerces-C {xerces_version}...')
        os.system(f'curl -L http://archive.apache.org/dist/xerces/c/3/sources/\
                xerces-c-{xerces_version}.tar.gz > xerces.tar.gz')
        with tarfile.open('xerces.tar.gz', 'r:gz') as tar:
            tar.extractall()
        os.remove('xerces.tar.gz')

        # Rename the extracted xerces directory to be the proper path
        xerces_version_folder = f'xerces-c-{xerces_version}'
        xerces_folder_simple = os.path.basename(os.path.normpath(xerces_path))
        os.rename(xerces_version_folder, xerces_folder_simple)

    def download_wxwidgets():
        # Download wxWidgets if it doesn't already exist
        if not os.path.exists(f'{wxWidgets_path}/wxWidgets-{wx_version}'):
            # Create & change directories
            if not os.path.exists(wxWidgets_path):
                os.mkdir(wxWidgets_path)
            os.chdir(wxWidgets_path)

            # Download wxWidgets source
            print(f'\nDownloading wxWidgets {wx_version}...')
            os.system(f'curl -L https://github.com/wxWidgets/wxWidgets/releases/download/\
                    v{wx_version}/wxWidgets-{wx_version}.tar.bz2 > wxWidgets.tar.bz2')
            with tarfile.open('wxWidgets.tar.bz2', 'r:bz2') as tar:
                tar.extractall()
            os.remove('wxWidgets.tar.bz2')

            # Make sure wxWidgets was downloaded
            if not os.path.exists(f'{wxWidgets_path}/wxWidgets-{wx_version}'):
                raise RuntimeError(f'Error in wxWidgets-{wx_version} download.')

    def download_cspice():
        # Download CSPICE if it doesn't already exist
        if os.path.exists(cspice_path):
            print('CSPICE already downloaded')
            return

        # Create & change directories
        os.makedirs(cspice_path, exist_ok=True)
        os.chdir(cspice_path)

        if sys.platform == 'darwin':
            cspice_type = 'MacIntel_OSX_AppleC'
        else:
            cspice_type = 'PC_Linux_GCC'

        print(f'\nDownloading {cspice_bit} CSPICE {cspice_version}...')
        if sys.platform == 'win32':
            # Download and extract Spice for Windows (32/64-bit)
            os.system(f'curl -L http://naif.jpl.nasa.gov/pub/naif/misc/toolkit_{cspice_version}\
                    /C/PC_Windows_VisualC_{cspice_bit}/packages/cspice.zip > cspice.zip')
            os.system(f'"{depends_path}/bin/7za/7za.exe" x cspice.zip > nul')
            os.chdir(cspice_path)  # cspice_path: depends/cspice for now
            os.rename('cspice', cspice_dir)

        else:  # Platform is not Windows
            # Download and extract Spice for Mac/Linux (32/64-bit)
            os.system(f'curl https://naif.jpl.nasa.gov/pub/naif/misc/toolkit_"{cspice_version}"/C/"\
                    {cspice_type}"_{cspice_bit}/packages/cspice.tar.Z > cspice.tar.Z')
            os.system('gzip -d cspice.tar.Z')
            os.system('tar -xf cspice.tar')
            os.system(f'mv cspice cspice_dir')
            os.remove('cspice.tar')

    def download_swig():
        # Download SWIG if it doesn't already exist
        # Check platform-appropriate path
        if sys.platform == 'win32':
            swig_dir = f'{swig_path}/swigwin'
        else:
            swig_dir = f'{swig_path}/swig'

        if os.path.exists(swig_dir):
            print('SWIG already downloaded')
            return

        # Create & change directories
        os.chdir(depends_path)
        os.makedirs(f'{depends_path}/swig', exist_ok=True)
        os.makedirs(swig_path, exist_ok=True)  # Duplication?
        os.chdir(swig_path)

        print(f'\nDownloading SWIG {swig_version}...')
        if sys.platform == 'win32':
            # Download and extract SWIG for Windows
            os.system(f'curl -L http://download.sourceforge.net/swig/swigwin-{swig_version}.zip\
                    > swig.zip')
            os.system(f'"{depends_path}/bin/7za/7za.exe" x swig.zip > nul')
            os.rename(f'swigwin-{swig_version}', 'swigwin')
            os.remove('swig.zip')
        else:
            # Download and extract SWIG for Mac/Linux
            os.system(f'curl -L http://download.sourceforge.net/swig/swig-{swig_version}.tar.gz\
                    > swig.tar.gz')
            os.system('gzip -d swig.tar.gz')
            os.system('tar -xf swig.tar')
            os.system(f'mv swig-{swig_version} swig')
            os.remove('swig.tar')

            # [GMT-6892] Download PCRE into SWIG directory
            print(f'\nDownloading PCRE {pcre_version} for use with SWIG...')
            os.chdir(swig_dir)
            os.system(f'curl -L https://sourceforge.net/projects/pcre/files/pcre\
                    /{pcre_version}/{pcre_filename}/download > {pcre_filename}')

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

        if sys.platform == 'darwin':
            java_os_name = 'mac'
        elif sys.platform == 'win32':
            java_os_name = 'windows'
        else:
            java_os_name = 'linux'

        java_base_url = f'https://github.com/AdoptOpenJDK/openjdk{java_major_version}\
            -binaries/releases/download/jdk-{java_full_version}/'
        java_url = f'{java_base_url}OpenJDK{java_major_version}U-jdk_x64_{java_os_name}\
            _hotspot_{java_version}_{java_update}'

        print(f'\nDownloading Java JDK {java_full_version}...')
        if sys.platform == 'win32':
            # Download and extract AdoptOpenJDK for Windows
            # print(f"curl command for Java download: curl -L '{java_url}.zip'")  # my code
            os.system(f'curl -L {java_url}.zip > jdk.zip')
            os.system(f'"{depends_path}/bin/7za/7za.exe" x jdk.zip > nul')
            os.rename(f'jdk-{java_full_version}', 'jdk')
            os.remove('jdk.zip')
        else:
            # Download and extract AdoptOpenJDK for Mac/Linux
            os.system(f'curl -L {java_url}.tar.gz > jdk.tar.gz')
            os.system('gzip -d jdk.tar.gz')
            os.system('tar -xf jdk.tar')
            os.system(f'mv jdk-{java_full_version} jdk')
            os.remove('jdk.tar')

    download_xerces()
    download_wxwidgets()
    download_cspice()
    download_swig()
    download_java()

    print("\nDependencies download complete")


def make_depend(dependency: str, install_type: str):
    dep_l = dependency.lower()  # convert name to lowercase
    install = 'install ' if install_type == 'install' else ''
    j_cores = f' -j{NCORES}' if 'build' in install_type else ''
    make_flag = os.system(f'make {install}{j_cores}> \
                            "{logs_path}/{dep_l}_{install_type}.log" 2>&1')
    if make_flag != 0:
        raise RuntimeError(f'{dependency} {install_type} build failed. Fix errors and try again.')


def build_xerces(plat: str):
    if not os.path.exists(xerces_path):
        raise FileNotFoundError(f'Xerces build cannot begin because the xerces folder was not found.'
                                f'\nCurrent working directory: {os.getcwd()}')

    print(f'\n********** Configuring Xerces-C++ {xerces_version} **********')

    # Windows-specific build
    if plat == 'win32':
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
            f'-Dtranscoder=windows -DCMAKE_INSTALL_PREFIX="{xerces_outdir}" "{xerces_path}" > '
            f'"{logs_path}\\xerces_cmake.log" 2>&1')

        print('-- Compiling debug Xerces. This could take a while...')
        os.system(f'cmake --build . --config Debug --target install > \
                    "{logs_path}\\xerces_build_debug.log" 2>&1')

        print('-- Compiling release Xerces. This could take a while...')
        os.system(f'cmake --build . --config Release --target install > '
                  f'"{logs_path}\\xerces_build_release.log" 2>&1')
        return

    # Out-of-source xerces build/install locations
    if sys.platform == 'darwin':
        xerces_build_path = f'{xerces_path}/cocoa-build'
        xerces_install_path = f'{xerces_path}/cocoa-install'
    else:
        xerces_build_path = f'{xerces_path}/linux-build'
        xerces_install_path = f'{xerces_path}/linux-install'

    # Find a test file to check if xerces has already been installed
    xerces_test_file = f'{xerces_install_path}/lib/libxerces-c.a'

    # Build xerces if the test file doesn't already exist
    if os.path.exists(xerces_test_file):
        print(f'Xerces {xerces_version} already configured')
        return

    os.mkdir(xerces_build_path)
    os.chdir(xerces_build_path)

    # For users who compile GMAT on multiple platforms side-by-side.
    # Running Windows configure.bat causes Mac/Linux configure scripts
    # to have missing permissions.
    os.system('chmod u+x ../configure')
    os.system('chmod u+x ../config/*')

    # Xerces needs flags on OSX
    macos_flags = '' if sys.platform != 'darwin' else \
        f'-mmacosx-version-min={osx_min_version} --sysroot={osx_sdk}'

    common_xerces_flags = ('--disable-shared --disable-netaccessor-curl'
                           ' --disable-transcoder-icu --disable-msgloader-icu')

    print(f'Configuring Xerces {xerces_version} debug library. This could take a while...')
    common_c_flags = f'-O0 -g -fPIC {macos_flags}'
    os.system(f'../configure {common_xerces_flags} CFLAGS="{common_c_flags}" CXXFLAGS=\
                "{common_c_flags}" --prefix="{xerces_install_path}" > \
                "{logs_path}/xerces_configure_debug.log" 2>&1')

    make_depend('xerces', 'build_debug')
    make_depend('xerces', 'install_debug')

    os.rename(f'{xerces_install_path}/lib/libxerces-c.a',
              f'{xerces_install_path}/lib/libxerces-cd.a')
    os.system('make clean > /dev/null 2>&1')

    print(f'Configuring Xerces {xerces_version} release library. This could take a while...')
    common_c_flags = f'-O2 -fPIC {macos_flags}'
    os.system(f'../configure {common_xerces_flags} CFLAGS="{common_c_flags}" \
                CXXFLAGS="{common_c_flags}" --prefix="{xerces_install_path}" \
                > "{logs_path}/xerces_configure_release.log" 2>&1')

    make_depend('xerces', 'build_release')
    make_depend('xerces', 'install_release')

    os.chdir('..')
    os.system(f'rm -Rf {xerces_build_path}')


def build_wxWidgets(plat: str):
    print(f'\n********** Configuring wxWidgets {wx_version} **********')

    # Windows-specific build
    if plat == 'win32':
        # Generate filenames to download
        wx_path = f'wxWidgets/wxWidgets-{wx_version}'
        os.chdir(depends_path)  # switch back to depends so later relative directory changes work

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

        def wxwidgets_build_command(build_type):
            return (f'nmake -f makefile.vc OFFICIAL_BUILD=1 COMPILER_VERSION='
                    f'{vc_major_version}{vc_minor_version} {wx_tgt_cpu} SHARED=1 BUILD={build_type}'
                    f' > "{logs_path}\\wxWidgets_build_{build_type}.log" 2>&1')

        print('-- Compiling debug wxWidgets. This could take a while...')
        os.system(wxwidgets_build_command('debug'))

        print('-- Compiling release wxWidgets. This could take a while...')
        os.system(wxwidgets_build_command('release'))

        os.chdir('../..')

        os.chdir('lib')
        os.rename(f'vc{vc_major_version}{vc_minor_version}{wx_type}.dll', f'vc{wx_type}.dll')

        os.chdir(depends_path)

        # Once the build has finished, vc_x64_dll needs to be copied into gmat/application/debug
        #  to enable Windows debug build. (See GMT-7534 https://gmat.atlassian.net/browse/GMT-7534)
        dll_name = 'wxmsw30ud_core_vc141_x64.dll'
        dll_source = f'{wxWidgets_path}/wxWidgets-{wx_version}/lib/vc_x64_dll/{dll_name}'
        dll_destination = f'{gmat_path}/application/debug/{dll_name}'
        shutil.copyfile(dll_source, dll_destination)

    else:  # running on something other than Windows
        # Set build path based on version
        wx_path = f'{wxWidgets_path}/wxWidgets-{wx_version}'

        wx_build_path = f'{wx_path}/{wx_platform_name}-build'
        wx_install_path = f'{wx_path}/{wx_platform_name}-install'
        wx_test_file = f'{wx_install_path}/lib/libwx_baseu-3.0.{wx_ext}'

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
        os.chdir(wx_build_path)

        print(f'Configuring wxWidgets {wx_version}. This could take a while...')

        macos_flags = ''
        if sys.platform == 'darwin':
            # wxWidgets 3.0.2 has a compile error due to an incorrect
            # include file on OSX 10.10+. Apply patch to fix this.
            # See [GMT-5384] and http://goharsha.com/blog/compiling-wxwidgets-3-0-2-mac-os-x-yosemite/
            osx_ver = mac_plat.mac_ver()[0]
            if wx_version == '3.0.2' and osx_ver > '10.10.0':
                os.system(f'sed -i.bk "s/WebKit.h/WebKitLegacy.h/" "{wx_path}/src/osx/webview_webkit.mm"')

            # wxWidgets needs these flags on OSX
            # NOTE on liblzma: The Mac build/test machine contains liblzma (via homebrew 'xz'), which conflicts with the wxWidgets build process
            macos_flags = f'--with-osx_cocoa --without-liblzma --with-macosx-version-min={osx_min_version} --with-macosx-sdk={osx_sdk}'

        os.system(f'../configure {macos_flags} --enable-unicode --with-opengl \
                    --prefix="{wx_install_path}" > "{logs_path}/wxWidgets_configure.log" 2>&1')

        # Compile, install, and clean wxWidgets
        make_depend('wxWidgets', 'build')
        make_depend('wxWidgets', 'install')
        os.chdir('..')
        os.system(f'rm -Rf "{wx_build_path}"')


def build_cspice(plat: str):
    print('\n********** Configuring CSPICE **********')

    def cspice_win():
        # Windows-specific build
        if sys.platform == 'win32':
            # Build CSPICE if cspiced.lib does not already exist
            if os.path.exists(f'{cspice_path}/{cspice_dir}/lib/cspiced.lib'):
                print('-- CSPICE already configured')
                return

            try:
                os.chdir(f'{cspice_path}/{cspice_dir}/src/cspice')
            except FileNotFoundError:
                print(f'build_cspice: Failed to switch to {cspice_path}/windows/cspice/src/cspice')
                print(f'cspice_path: {cspice_path}')
                print(f'Current working directory: {os.getcwd()}')
                print(f'Directory contents: {os.listdir()}')
                raise

            def compile_cspice(build_type):
                print(f'-- Compiling {build_type} CSPICE. This could take a while...')
                os.system(f'cl /c /DEBUG /Z7 /MP -D_COMPLEX_DEFINED -DMSDOS'
                          f' -DOMIT_BLANK_CC -DNON_ANSI_STDIO -DUIOLEN_int *.c >'
                          f' "{logs_path}\\cspice_build_{build_type}.log" 2>&1')
                os.system(f'link -lib /out:..\\..\\lib\\cspiced.lib *.obj >> '
                          f'"{logs_path}\\cspice_build_{build_type}.log" 2>&1')

                os.system('del *.obj')

            compile_cspice('debug')
            compile_cspice('release')

            os.chdir(depends_path)

            return

    if plat == 'windows':
        cspice_win()
        return

    # Windows would have returned or thrown error so below is macOS/Linux specific
    spice_path = cspice_path + f'/{cspice_dir}'
    tk_compile_arch = f'-m{cspice_bit}'
    os.system(f'export TKCOMPILEARCH="{tk_compile_arch}"')

    flags = '' if sys.platform != 'darwin' else f'-mmacosx-version-min={osx_min_version} -Wno-error=implicit-function-declaration --sysroot={osx_sdk}'

    # if sys.platform == 'darwin':  # macOS
    #     macos_flags = f'-mmacosx-version-min={osx_min_version} -Wno-error=implicit-function-declaration --sysroot={osx_sdk}'
    # else:
    #     macos_flags = ''

    cspice_test_file = f'{spice_path}/lib/cspiced.a'

    if os.path.exists(cspice_test_file):
        print('-- CSPICE already configured')
    else:
        os.chdir(f'{spice_path}/src/cspice')

    # Compile debug CSPICE with integer uiolen [GMT-5044]
    print('Compiling CSPICE debug library. This could take a while...')
    os.environ['TKCOMPILEOPTIONS'] = f'{tk_compile_arch} -c -ansi {flags} \
        -g -fPIC -DNON_UNIX_STDIO -DUIOLEN_int'
    make_flag = os.system(f'./mkprodct.csh > "{logs_path}/cspice_build_debug.log" 2>&1')

    if make_flag == 0:
        os.system('mv ../../lib/cspice.a ../../lib/cspiced.a')
    else:
        print('CSPICE debug build failed. Fix errors and try again.')

    # Compile release CSPICE with integer uiolen [GMT-5044]
    print('Compiling CSPICE release library. This could take a while...')
    os.environ['TKCOMPILEOPTIONS'] = f'{tk_compile_arch} -c -ansi {flags} \
        -O2 -fPIC -DNON_UNIX_STDIO -DUIOLEN_int'
    make_flag = os.system(f'./mkprodct.csh > "{logs_path}/cspice_build_release.log" 2>&1')

    if make_flag != 0:
        print('CSPICE release build failed. Fix errors and try again.')


def build_swig(plat: str):
    # Windows is pre-built
    if plat == 'windows':
        print('\n-- SWIG for Windows comes pre-built')
        return

    print('\n********** Configuring SWIG **********')

    # Out-of-source SWIG build/install locations
    swig_dir = f'{swig_path}/swig'

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
    os.system(f'../Tools/pcre-build.sh > "{logs_path}/pcre_build.log" 2>&1')

    # For users who compile GMAT on multiple platforms side-by-side.
    # Running Windows configure.bat causes Mac/Linux configure scripts
    # to have missing permissions.
    os.system('chmod u+x ../configure')

    print(f'Configuring SWIG {swig_version} tool. This could take a while...')
    os.system(f'../configure --prefix="{swig_install_path}" > \
                "{logs_path}/swig_configure.log" 2>&1')

    make_depend('SWIG', 'build')
    make_depend('SWIG', 'install')

    os.chdir('..')
    os.system(f'rm -Rf {swig_build_path}')


cspice_version = 'N0067'
swig_version = '4.0.2'
pcre_version = '8.45'
java_version = '11.0.5'
java_update = '10'
wx_version = '3.0.4'
xerces_version = '3.2.2'
osx_min_version = '10.15'
osx_sdk = '/Library/Developer/CommandLineTools/SDKs/MacOSX10.15.sdk'
vs_version = 2022
vs_major_version = '17'
vc_major_version = '14'
vc_minor_version = '1'

gmat_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # Path to gmat folder
depends_path = str(f'{gmat_path}/depends')  # Path to depends folder
logs_path = f'{depends_path}/logs'  # Path to depends/logs folder

# Create path variables
bin_path = f'{depends_path}/bin'
f2c_path = f'{depends_path}/f2c'
cspice_path = f'{depends_path}/cspice'
swig_path = f'{depends_path}/swig'
java_path = f'{depends_path}/java'
wxWidgets_path = f'{depends_path}/wxWidgets'
xerces_path = f'{depends_path}/xerces'
sofa_path = f'{depends_path}/sofa'
tsplot_path = f'{depends_path}/tsPlot'

platform = sys.platform
# Platform-based setup
if platform == 'win32':
    PLATFORM_NAME = 'windows'
    swig_dir = f'{swig_path}/swigwin'
    setup_windows()
else:
    if platform == 'darwin':
        PLATFORM_NAME = 'macosx'

        cmake_platform_name = 'cocoa'
        wx_platform_name = 'cocoa'
        swig_platform_name = 'cocoa'

        wx_ext = 'dylib'

    else:
        PLATFORM_NAME = 'linux'
        cmake_platform_name = 'linux'
        wx_platform_name = 'gtk'
        swig_platform_name = 'linux'
        wx_ext = 'so'

cspice_path = f'{cspice_path}/{PLATFORM_NAME}'
java_path = f'{java_path}/{PLATFORM_NAME}'

if struct.calcsize("P") * 8 == 32:
    # TODO Fill with any lines that ask about CPU bit-ness
    wx_type = '_'
    wx_tgt_cpu = ''
    cspice_bit = '32'
else:  # assume 64-bit
    wx_type = '_x64_'
    wx_tgt_cpu = 'TARGET_CPU=X64'
    cspice_bit = '32'

# Set up dir/file names for downloaded files
cspice_dir = f'cspice{cspice_bit}'
pcre_filename = f'pcre-{pcre_version}.tar.gz'

# Get number of cores for multithreaded compilation
NCORES = str(os.cpu_count())
if NCORES == 'None':
    NCORES = '1'

print('\n*** Configuring GMAT dependencies ***\n')

# Create log directory
if not os.path.exists(logs_path):
    os.mkdir(logs_path)

download_depends()  # download GMAT dependencies (Xerces, wxWidgets, CSPICE, SWIG)

# Build the dependencies using CMake
build_xerces(platform)
build_wxWidgets(platform)
build_cspice(platform)
build_swig(platform)

print('\n*** Done configuring GMAT dependencies ***\n')
