#!/usr/bin/python3

import logging.config

from webcrawler.crawler import Crawler

logging.config.fileConfig ( fname='.logging.conf', disable_existing_loggers=False )

def print_dfs_urls ( url_node, level=0 ):
    """
    print urls in dfs manner
    :param url_node: An instance of UrlNode
    :param level:current level in UrlTree (int)
    :return:
    """
    if not url_node: return

    dash = ""
    for i in range ( 4 * level ):
        dash += "-"
    text = dash + str ( url_node.url )

    fd.write(text+"\n")
    print ( text )

    for child_url in url_node.child_urls:
        print_dfs_urls ( child_url, level + 1 )

c = Crawler ( domain_name="http://www.divyabhaskarofara.org/", output_file_name="output.txt", num_threads=4 )
c.wait_for_urlparse_threads()

fd = open ( file="./outputs/output.txt", mode='a' )
print_dfs_urls ( c.urlnode_parse_root )

fd.close()
