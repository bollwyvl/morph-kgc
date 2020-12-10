import argparse, os, re, logging
import multiprocessing as mp
from configparser import ConfigParser, ExtendedInterpolation


def _configure_logger(config, level=logging.INFO):
    """
    Configures the logger based on input arguments. If no logging argument is provided, log level is set to WARNING.

    :param config: the ConfigParser object
    :type config: configparser
    :param level: logging level to use
    """

    if config.has_option('CONFIGURATION', 'logs'):
        logging.basicConfig(filename=config.get('CONFIGURATION', 'logs'),
                            format='%(levelname)s | %(asctime)s | %(message)s', filemode='w', level=level)
    else:
        logging.basicConfig(level=logging.WARNING)


def _dir_path(dir_path):
    """
    Checks that a directory exists. If the directory does not exist, it creates the directories in the path.

    :param dir_path: the path to the directory
    :type dir_path: str
    :return valid path to the directory
    :rtype str
    """

    dir_path = str(dir_path)
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)

    return dir_path


def _file_path(file_path):
    """
    Checks that directories in a file path exist. If they do not exist, it creates the directories.

    :param file_path: the path to the file
    :type file_path: str
    :return the path to the file
    :rtype str
    """

    file_path = str(file_path).strip()
    if not os.path.exists(os.path.dirname(file_path)):
        if os.path.dirname(file_path):
            os.makedirs(os.path.dirname(file_path))

    return file_path


def _file_name(file_name):
    """
    Generates a valid file name from an input file name.

    :param file_name: the original file name
    :type file_name: str
    :return the valid file name
    :rtype str
    """

    file_name = str(file_name).strip()
    file_name.replace(' ', '_')
    file_name = re.sub(r'(?u)[^-\w.]', '', file_name)

    return file_name


def _existing_file_path(file_path):
    """
    Checks if a file exists.

    :param file_path: the file path
    :type file_path: str
    :return the file path
    :rtype str
    """

    file_path = str(file_path).strip()
    if not os.path.isfile(file_path):
        raise argparse.ArgumentTypeError("%r is not a valid file path." % file_path)

    return file_path


def _processes_number(number):
    """
    Generates a natural number from a given number. Number is converted to int.
    In case of been 0, the number of cores in the system is generated.

    :param number: number
    :type number: str
    :return natural number
    :rtype int
    """

    whole_number = int(number)
    if whole_number < 0:
        raise ValueError
    elif whole_number == 0:
        whole_number = mp.cpu_count()

    return whole_number


def _natural_number_including_zero(number):
    """
    Generates a natural number (including zero) from a given number.

    :param number: number
    :type number: str
    :return natural number (including zero)
    :rtype int
    """

    whole_number = int(number)
    if whole_number < 0:
        raise ValueError

    return whole_number


def _validate_config_data_sources_sections(config):
    raise ValueError('TODO: validate data sources section')

    for section in config.sections():
        if section != 'CONFIGURATION':
            ''' if section is not configuration then it is a data source.
                Mind that DEFAULT section is not triggered with config.sections(). '''
            #data_sources[section] = dict(config.items(section))
            pass

    return config


def _validate_config_configuration_section(config):
    """
    Validates that the configuration section in the config file is correct.

    :param config: config object
    :type config: configparser
    :return config object with validated configuration section
    :rtype configparser
    """

    config.set('CONFIGURATION', 'output_dir', _dir_path(config.get('CONFIGURATION', 'output_dir')))

    # output_file has no default value, it is needed to check if it is in the config
    if config.has_option('CONFIGURATION', 'output_file'):
        config.set('CONFIGURATION', 'output_file', _file_name(config.get('CONFIGURATION', 'output_file')))

    remove_duplicates = config.getboolean('CONFIGURATION', 'remove_duplicates')
    push_down_distincts = config.getboolean('CONFIGURATION', 'push_down_distincts')
    if not remove_duplicates and push_down_distincts:
        error_msg = 'Option remove_duplicates=' + remove_duplicates + ' but option push_down_distincts=' \
                    + push_down_distincts + '. If duplicates are not to be removed, then ' \
                                            'pushing down distincts is not valid.'
        raise ValueError(error_msg)

    mapping_partitions = config.get('CONFIGURATION', 'mapping_partitions')
    mapping_partitions = str(mapping_partitions).lower().strip()
    valid_options = ['', 's', 'p', 'sp']
    if mapping_partitions not in valid_options:
        raise ValueError('Option mapping_partitions must be in: ' + str(valid_options))

    config.set('CONFIGURATION', 'number_of_processes',
               str(_processes_number(config.get('CONFIGURATION', 'number_of_processes'))))

    config.set('CONFIGURATION', 'chunksize',
               str(_natural_number_including_zero(config.get('CONFIGURATION', 'chunksize'))))

    # logs has no default value, it is needed to check if it is in the config
    if config.has_option('CONFIGURATION', 'logs'):
        config.set('CONFIGURATION', 'logs', _file_path(config.get('CONFIGURATION', 'logs')))

    return config


def _complete_config_file_with_args(config, args):
    """
    Completes missing options in the config file with the options provided via arguments.
    Options specified in the config file are prioritized, i.e., if the option is specified in
    the config file the option in the arguments is ignored.

    :param config: the ConfigParser object
    :type config: argparse
    :param args: the argparse object
    :type args: configparser
    :return ConfigParser object extended with information from arguments
    :rtype configparser
    """

    ''' Create section CONFIGURATION if it does not exist in the config file '''
    if not config.has_section('CONFIGURATION'):
        config.add_section('CONFIGURATION')

    ''' If parameters are not provided in the config file, take them from arguments.
        mind that ConfigParser store options as strings'''
    if not config.has_option('CONFIGURATION', 'output_dir'):
        config.set('CONFIGURATION', 'output_dir', args.output_dir)
    # output_file has no default value, it is needed to check if it is in the args
    if not config.has_option('CONFIGURATION', 'output_file') and 'output_file' in args:
        config.set('CONFIGURATION', 'output_file', args.output_file)
    if not config.has_option('CONFIGURATION', 'remove_duplicates'):
        config.set('CONFIGURATION', 'remove_duplicates', str(args.remove_duplicates))
    if not config.has_option('CONFIGURATION', 'push_down_distincts'):
        config.set('CONFIGURATION', 'push_down_distincts', str(args.push_down_distincts))
    if not config.has_option('CONFIGURATION', 'mapping_partitions'):
        config.set('CONFIGURATION', 'mapping_partitions', args.mapping_partitions)
    if not config.has_option('CONFIGURATION', 'number_of_processes'):
        config.set('CONFIGURATION', 'number_of_processes', str(args.number_of_processes))
    if not config.has_option('CONFIGURATION', 'chunksize'):
        config.set('CONFIGURATION', 'chunksize', str(args.chunksize))
    # logs has no default value, it is needed to check if it is in the args
    if not config.has_option('CONFIGURATION', 'logs') and 'logs' in args:
        config.set('CONFIGURATION', 'logs', args.logs)

    return config


def _parse_arguments():
    """
    Parses command line arguments of the engine.

    :return parsed arguments
    """

    parser = argparse.ArgumentParser(
        description='Generate knowledge graphs from heterogeneous data sources.',
        epilog='Transform data into knowledge.',
        allow_abbrev=False,
        argument_default=argparse.SUPPRESS
    )

    parser.add_argument('-c', '--config', type=_existing_file_path, required=True,
                        help='Path to the configuration file.')
    parser.add_argument('-d', '--output_dir', default='output', type=str,
                        help='Path to the directory storing the results.')
    parser.add_argument('-f', '--output_file', type=str,
                        help='If a file name is specified, all the results will be stored in this file. '
                             'If no file is specified the results will be stored in multiple files.')
    parser.add_argument('-r', '--remove_duplicates', default='no', type=str,
                        choices=['yes', 'no', 'on', 'off', 'true', 'false', '0', '1'],
                        help='Whether to remove duplicated triples in the results.')
    parser.add_argument('-p', '--mapping_partitions', nargs='?', default='', const='sp',
                        choices=['s', 'p', 'sp'],
                        help='Partitioning criteria for mappings. s for using subjects and p for using predicates. If '
                             'this parameter is not provided, no mapping partitions will be considered.')
    parser.add_argument('--push_down_distincts', default='no', type=str,
                        choices=['yes', 'no', 'on', 'off', 'true', 'false', '0', '1'],
                        help='Whether to retrieve distinct results from data sources.')
    parser.add_argument('--number_of_processes', default=1, type=_processes_number,
                        help='Number of parallel processes. 0 to set it to the number of CPUs in the system.')
    parser.add_argument('--chunksize', default=0, type=_natural_number_including_zero,
                        help='Maximum number of rows of data processed at once by a process.')
    parser.add_argument('-l', '--logs', nargs='?', const='', type=str,
                        help='File path to write logs to. If no path is provided logs are redirected to stdout.')
    parser.add_argument('-v', '--version', action='version', version='Morph-RDFizer 0.1')

    return parser.parse_args()


def parse_config():
    """
    Parses command line arguments and the config file. It also validates that values are correct.
    Arguments in the config file have more priority than command line arguments, if specified, command line
    arguments will overwrite config file ones. Logger is configured.

    :return config object populated with command line arguments and config file arguments,
    :rtype configparser
    """

    args = _parse_arguments()

    config = ConfigParser(interpolation=ExtendedInterpolation())
    config.read(args.config)
    config = _complete_config_file_with_args(config, args)

    config = _validate_config_configuration_section(config)
    _configure_logger(config)
    config = _validate_config_data_sources_sections(config)

    return config