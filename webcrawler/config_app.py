import logging

import dflt_cfg
from webcrawler.app_constant import *


class UserConfig:
    """
    This class contains functions, which enable command line arguments and verify the \
    options entered by user and finally enforces the valid options throughout the application, \
    by also storing them in dflt_cfg.
    """

    def __init__ ( self ):
        self.logger = logging.getLogger ( __name__ )

    @staticmethod
    def set_app_config ( ):
        """
        Enable and configure user and application settings
        :return:
        """
        user_args = UserConfig.get_cmdline_args ( )
        UserConfig.verify_update_cfg ( user_args )

    @staticmethod
    def get_cmdline_args ( test_args=[ ] ):
        """
        This function enables command line arguments for application usages. test_args parameter of this function \
        is supposed to be used for unittest purpose of this function.
        :param test_args: only used for testing argparse  capability to parse command-line arguments
        :return: argument entered by users (type: <class 'argparse.Namespace'>)
        """
        import argparse
        parser = argparse.ArgumentParser ( description='Domain Crawler - Domain Mapping' )
        parser._optionals.title = "optional arguments (For an invalid arg value, default value will be picked up)"
        parser.add_argument ( '-nt', '--nthread', dest='n_thread', required=False, metavar='N',
                              default=4, type=int, help='number of threads (N>=0: default=4)' )

        parser.add_argument ( '-l', '--log', dest='log_lvl', required=False, metavar='L',
                              default=2, type=int, help='log level (0<=L<=5: default=2)' )

        parser.add_argument ( '-t', '--timeout', dest='timeout', required=False, metavar='T',
                              default=10, type=int, help='timeout in seconds (T>=0: default=10)' )

        parser.add_argument ( '-f', '--file', dest='op_f_name', required=False, metavar="File_Name",
                              default="output.txt", type=str, help='name of the output file (default=output.txt): '
                                                                   '\ stored in output dir' )

        required = parser.add_argument_group ( 'required arguments' )

        required.add_argument ( '-d', '--domain', dest='domain_name', required=True, metavar="Domain",
                                type=str, help='name of the domain' )

        if test_args:
            args = parser.parse_args ( test_args )
        else:
            args = parser.parse_args ( )

        return args

    @staticmethod
    def verify_update_cfg ( args ):
        """
        Verify the argparse value entered by user. If the values provided by user \
        are valid, then they also overwrite control options in dflt_cfg; otherwise dflt_cfg \
        values remains active.
        :param args: argparse value entered by user (type: <class 'argparse.Namespace'>)
        :return:
        """
        n_threads = args.n_thread
        # verification of number of threads entered by user
        if n_threads >= 0:
            # storing value of number of threads in cfg for future use
            dflt_cfg.DFLT_CFG[ NUM_THREADS ] = n_threads

        usr_log_lvl = args.log_lvl
        # verify and set the log level value entered by user
        UserConfig.set_verify_log_level ( usr_log_lvl )

        app_timeout = args.timeout
        # verify and set the application timeout value entered by user
        if app_timeout < 0:
            app_timeout = 10  # seconds
        dflt_cfg.DFLT_CFG[ TIMEOUT ] = app_timeout

        # config output file path
        op_file_name = args.op_f_name
        dflt_cfg.DFLT_CFG[ OUTPUT_PATH ] = "./output/" + op_file_name

        # config domain name in dflt_cfg
        domain_name = args.domain_name
        dflt_cfg.DFLT_CFG[ DOMAIN ] = domain_name

    @staticmethod
    def set_verify_log_level ( user_log_level ):
        """
        This function verifies and set the log level of this application using the log level provided by \
        user as args through cmdline. if the cmdline provided log level is invalid, then \
        by default, application chooses INFO level logging.
        :param user_log_level: log level provided by user as args through cmd line (int)
        :return:
        """
        # Reference: https://docs.python.org/2/howto/logging.html#logging-levels
        std_logging_levels = {
            0: logging.NOTSET,  # lowest priority
            1: logging.DEBUG,
            2: logging.INFO,
            3: logging.WARNING,
            4: logging.ERROR,
            5: logging.CRITICAL,  # highest priority
        }

        mapped_log_level = std_logging_levels.get ( user_log_level )
        if not mapped_log_level:  # default log level
            user_log_level = 2
            mapped_log_level = std_logging_levels[ user_log_level ]

        # storing log level in dflt_cfg
        dflt_cfg.DFLT_CFG[ LOG_LEVEL ] = user_log_level

        # setting log level of application
        logging.getLogger ( ).setLevel ( mapped_log_level )
