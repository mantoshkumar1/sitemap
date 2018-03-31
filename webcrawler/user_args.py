import logging


class UserArgs:
    """
    This class will implement functionality which will allow users to provide following values from command prompt.

    num_threads: optional (default: 4) (must be > 0)
    log level : optional (valid values: 0<=x<=5) (default: 2)
    timeout: optional (valid > 0) default = 10. and can't be None.
    domain_name: mandatory (str)
    output file name: mandatory (str)

    for example:
    python create_sitemap.py -t 4 -l 2 -t 10 -d "https://monzo.com/" -o "monzo.txt"
    """

    def __init__ ( self ):
        self.logger = logging.getLogger ( __name__ )
