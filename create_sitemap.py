#!/usr/bin/python3
#import logging
import logging.config
from webcrawler.crawler import Crawler

logging.config.fileConfig (fname='.logging.conf', disable_existing_loggers=False)

test = Crawler()