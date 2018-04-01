#!/usr/bin/python3

import logging.config

from webcrawler.crawler import Crawler
from webcrawler.config_app import UserConfig
from webcrawler.urlparse import UrlTree

logging.config.fileConfig ( fname='.logging.conf', disable_existing_loggers=False )

# First Configuring application as per need of user's command line arguments
UserConfig.set_app_config()

# Crawling domain
crwlr = Crawler ( )
crwlr.start_url_parsing()
urlnode_root = crwlr.release_urlparse_resources()

# Using tree hierarchy to produce result in output file
url_parse_tree = UrlTree(urlnode_root)
url_parse_tree.write_sitemap()

print ( "-------------------------------------------------------------------" )
print ( "<<Thank you for using Domain Crawler - Domain Mapping application>>" )
print ( "-------------------------------------------------------------------" )