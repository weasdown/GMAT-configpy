# Version of configure.py that supports specifying build parameters as command line arguments
import sys
import os
import json

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

if __name__ == '__main__':
    print('*** GMAT compilation configuration wizard ***')
    plat = sys.platform
    print(f'Your current platform is: {plat}')


    def options_bullets(options: dict) -> str:
        output: str = ''
        for item in list(options.items())[1:]:
            output += f'\n\t{item[0]}: {item[1]}'
        return output


    def prompt(allowed_values: dict, prompt_text: str, print_selection: bool = False):
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

        # except ValueError:
        #     print('Selection must be specified as an integer')
        #     prompt(allowed_values, prompt_text)

        except Exception as ex:
            raise


    def check_py_debug_libs(py_vers: list[str]) -> bool:
        print('Specified options include debug configuration and Python API. Checking Python debug libs...')
        platform = sys.platform
        if platform != 'win32':
            print('Current platform is not Windows so no problem.')
            return True
        else:
            appdata_local = os.getenv('LOCALAPPDATA')
            for ver in py_vers:
                ver_num = ver.replace('.', '')
                py_root = f'{appdata_local}/Programs/Python/Python{ver_num}/libs'
                debug_lib = f'python{ver_num}_d.lib'
                if not os.path.isfile(f'{py_root}/{debug_lib}'):
                    raise FileNotFoundError(f'Could not find debug lib for Python {ver}')
                else:
                    print(f'\t- Found debug lib for Python {ver}')


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
            vers = ','.join([f'{major_ver}.{minor}' for minor in range(minor_ver_min, minor_ver_max+1)])
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


    config_values = {'default': 1, 1: 'release only', 2: 'debug only', 3: 'debug and release'}
    api_values = {'default': 1, 1: 'None', 2: 'Python only', 3: 'Java only', 4: 'Python and Java'}

    config, config_desc = prompt(config_values, 'a build configuration')
    api, api_desc = prompt(api_values, 'which API(s) to build')

    if 'Python' in api_desc:
        py_versions = py_ver_prompt()

        if 'debug' in config_desc:
            check_py_debug_libs(py_versions)

    if 'Java' in api_desc:
        raise NotImplementedError

    print(f'Setting up configuration "{config_desc}" '
          f'{f"with APIs {api_desc}" if api_desc != "None" else "without APIs"}')
