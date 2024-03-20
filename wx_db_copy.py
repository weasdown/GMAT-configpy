# Test script to copy contents of {GMAT}\depends\wxWidgets\wxWidgets-3.0.4\lib\vc_x64_dll into {GMAT}\application\debug
# to enable Windows debug build. (See GMT-7534 https://gmat.atlassian.net/browse/GMT-7534)

import os
import shutil

'C:/Users/WillliamEasdown/GMAT-local/Comp/gR22a-src/GMAT-R2022a/depends'
gmat_path = os.path.dirname(os.path.abspath(os.getcwd()))  # Path to gmat folder
depends_dir = str(f'{gmat_path}/depends')  # Path to depends folder
app_debug_dir = f'{gmat_path}/application/debug'

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
wxwidgets_path = depends_paths['wxWidgets']


version = versions['wxWidgets']
wx_db_source = f'{wxwidgets_path}/wxWidgets-{version}/lib/vc_x64_dll'
files = os.listdir(wx_db_source)
for file in files:
    shutil.copytree(wx_db_source, app_debug_dir, dirs_exist_ok=True)
    print(f'{file} copied')

print('\nDone')
