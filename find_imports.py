import ast
import pathlib
import sys
import importlib.util
from stdlib_list import stdlib_list
import logging

def imported_modules(f, baseonly):
    logging.debug(f.name)
    if baseonly:
        filt = lambda x: x.split('.')[0]
    else:
        filt = lambda x: x
    modules = set()
    
    try:
        tree = ast.parse(f.read())
    except SyntaxError:
        return modules

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                modules.add(filt(alias.name))
        if isinstance(node, ast.ImportFrom):
            modules.add(filt(node.module))
    return modules

def localmodule(module):
    try:
        spec = importlib.util.find_spec(module)
    except ModuleNotFoundError:
        logging.debug(f'Module not found: {module}')
        return False
    except ValueError:
        logging.debug(f'ValueError: {module}')        
        return False
    except AttributeError:
        logging.debug(f'AttributeError: {module}')
        return False
    if spec is None:
        logging.debug(f'Spec was none for {module}')
        return False

    modulepath = pathlib.Path(spec.origin)
    logging.debug(f'{module}: {modulepath}')
    return pathlib.Path.cwd() in modulepath.parents

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser('Find imports in files')
    parser.add_argument('files', nargs="+", type=argparse.FileType('r'),
                        help='Files to parse')
    parser.add_argument('--stdlib', action='store_false', 
                        help='Include modules from the standard libary')
    parser.add_argument('--local', action='store_true',
                        help='Include local modules')
    parser.add_argument('--stdlibversion', default='3.5',
                        choices=["2.6", "2.7", "3.2", "3.3", "3.4", "3.5"],
                        help='Python standard library version')
    parser.add_argument('--debug', action='store_true',
                        help='Debug level logging')
    parser.add_argument('--baseonly', action='store_true',
                        help='Only find base module (reports celery.task as celery)')

    args=parser.parse_args()

    if args.debug:
        logging.basicConfig(level=logging.DEBUG)

    if args.stdlib:
        stdlibmodules = set(stdlib_list(args.stdlibversion))
    else:
        stdlibmodules = set()

    modules = set()

    for f in args.files:
        modules.update(imported_modules(f, args.baseonly))

    sys.path.append(str(pathlib.Path.cwd()))

    for module in modules - stdlibmodules:
        logging.debug(f'Looking up {module}')
        local = localmodule(module)
        if (local and args.local) or not local:
            print(module)
