# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import logging
import os
import sys

from iris.api.core.util.core_helper import get_module_dir
from parse_args import parse_args


logger = logging.getLogger(__name__)


def get_tests_from_text_file(arg):
    test_list = []
    test_packages = []

    if os.path.isfile(arg):
        logger.debug('"%s" found. Proceeding ...' % arg)
        with open(arg, 'r') as f:
            test_paths_list = [line.strip() for line in f]
        if len(test_paths_list) == 0:
            logger.error('"%s" does not contain any valid test paths. Exiting program ...' % str(arg))
            return test_list, test_packages
        logger.debug('Tests found in the test suite file:\n\n%s\n' % '\n'.join(map(str, test_paths_list)))
        logger.debug('Validating test paths ...')
        for test_path in test_paths_list:
            if os.path.isfile(test_path):
                logger.debug('"%s" is a valid test path. Proceeding ...' % test_path)
                test_list.append(os.path.splitext(os.path.basename(test_path))[0])
                test_packages.append(os.path.dirname(test_path))
            else:
                logger.warning('"%s" is not a valid test path. Skipping ...' % test_path)

        if len(test_list) == 0:
            logger.error('"%s" does not contain any valid test paths. Exiting program ...' % str(arg))
            return test_list, test_packages
    else:
        logger.error('Could not locate "%s" . Exiting program ...', str(arg))
        return test_list, test_packages
    logger.debug('List of tests to execute: [%s]' % ', '.join(map(str, test_list)))
    return test_list, test_packages


def get_tests_from_list(arg):
    test_list = []
    test_packages = []
    tests = [str(item + ('.py' if not item.endswith('.py') else '')).strip() for item in arg.split(',')]
    tests_directory = parse_args().directory

    for test in tests:
        for dir_path, sub_dirs, all_files in os.walk(tests_directory):
            if test in all_files:
                test_list.append(os.path.splitext(test)[0])
                test_packages.append(os.path.join(os.path.split(__file__)[0], dir_path.strip()))
        if os.path.splitext(test)[0] not in test_list:
            logger.warning('Could not locate %s' % test)
    if len(test_list) == 0:
        logger.error('No tests to run. Exiting program ...')
    return test_list, test_packages


def get_tests_from_directory(arg):
    test_list = []
    test_packages = []
    if os.path.isdir(arg):
        tests_directory = arg
    else:
        tests_root_folder = os.path.join(get_module_dir(), 'iris', 'tests')
        tests_directory = os.path.join(tests_root_folder, arg.strip())

    if os.path.isdir(tests_directory):
        logger.debug('Path %s found. Checking content ...', tests_directory)
        for dir_path, sub_dirs, all_files in os.walk(tests_directory):
            for current_file in all_files:
                if current_file.endswith('.py') and not current_file.startswith('__'):
                    test_list.append(os.path.splitext(current_file)[0])
                    if dir_path not in test_packages:
                        test_packages.append(dir_path)
        if len(test_list) == 0:
            logger.error('Directory %s does not contain test files. Exiting program ...' % tests_directory)
            return test_list, test_packages
        else:
            logger.debug('Test packages: %s', test_packages)
            logger.debug('List of tests to execute: [%s]' % ', '.join(map(str, test_list)))
            return test_list, test_packages
    else:
        logger.error('Path: %s does not exist. Exiting program ...' % tests_directory)
        return test_list, test_packages


def load_tests(app):
    """Test loading

    Test loading is done by providing a list of test names separated by comma, a path to a file containing a custom list
    of tests or a directory. The provided list of test names can be with or without .py extension.

    The path to the file that contains the list of tests should have .txt extension. The full path is needed. For
    example: '/Users/user_name/full_path/test_suite.txt'. The content of the file should be a simple line-delimited list
    of test paths (full path required including file extensions).
    """

    app.test_list = []
    app.test_packages = []

    if app.args.rerun:
        path = os.path.join(app.args.workdir, 'runs', 'last_fail.txt')
        app.args.test = path
        logger.info('Re-running failed tests from previous run.')

    if app.args.test:
        if app.args.test.endswith('.txt'):
            app.test_list, app.test_packages = get_tests_from_text_file(app.args.test)
        else:
            app.test_list, app.test_packages = get_tests_from_list(app.args.test)
    elif app.args.directory:
        app.test_list, app.test_packages = get_tests_from_directory(app.args.directory)

    for package in app.test_packages:
        sys.path.append(package)

    if len(app.test_list) == 0:
        app.finish(code=1)