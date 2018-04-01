import logging

import dflt_cfg
from webcrawler.app_constant import OUTPUT_PATH, DOMAIN


class UrlNode:
    """
    This class represents an URL and its children
    """
    def __init__ ( self, url ):
        """
        :param url: str
        """
        self.logger = logging.getLogger ( __name__ )

        # an url in str format
        self.url = url

        # each element in child_urls contains an instance of UrlNode
        self.child_urls = set ( )


class UrlTree:
    """
    This class contains the UrlNode(s) as tree hierarchy
    """
    def __init__ ( self, root ):
        """
        :param root: an instance of UrlNode which represents the root of UrlTree
        """
        self.logger = logging.getLogger ( __name__ )

        # root urlnode of the urltree hierarchy
        self.root = root

        # file pointer to the output file
        self.output_fd = None

    def write_sitemap ( self ):
        """
        This function opens the output file and writes the sitemap into that and finally closes it safely.
        :return:
        """
        try:
            self.output_fd = open ( file=dflt_cfg.DFLT_CFG[ OUTPUT_PATH ], mode='w' )
            self.print_url_links ( self.root )
        except (PermissionError, AttributeError) as err:
            self.logger.error ( "Error {0} occurred. Output file {1} cannot be created".format ( err, \
                                                                                                        dflt_cfg.DFLT_CFG[
                                                                                                            OUTPUT_PATH ] ) )
        except Exception as err:
            self.logger.error ( "Error {0} occurred while writing sitemap in output file: {1}".format ( err, \
                                                                                                        dflt_cfg.DFLT_CFG[ OUTPUT_PATH ] ) )
            self.output_fd.close ( )
        else:
            print("Sitemap for {} is written in {}.".format(dflt_cfg.DFLT_CFG[DOMAIN], dflt_cfg.DFLT_CFG[ OUTPUT_PATH ]))
            print( "Logs (Broken or dead URLs along with application logs) for domain {0} are available in {1} directory.".format ( dflt_cfg.DFLT_CFG[DOMAIN], "./logs" ) )
            self.output_fd.close ( )

    def print_url_links ( self, url_node, level=0 ):
        """
        print urls in recursiveDescription manner using dfs
        :param url_node: An instance of UrlNode
        :param level:current level in UrlTree (int)
        :return:
        """
        if not url_node: return

        dash = ""
        for i in range ( 4 * level ):
            dash += "."
        url_text = dash + str ( url_node.url )

        self.output_fd.write ( url_text + "\n" )

        for child_url in url_node.child_urls:
            self.print_url_links ( child_url, level + 1 )
