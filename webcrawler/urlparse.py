import logging


class UrlNode:
    def __init__ ( self, url ):
        self.logger = logging.getLogger ( __name__ )

        # url in str format
        self.url = url

        # each element in child_urls contains an instance of UrlNode
        self.child_urls = set()
