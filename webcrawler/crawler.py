# https://pymotw.com/3/urllib.parse/#parsing
# Uniform Resource Identifiers (URI): Generic Syntax: https://tools.ietf.org/html/rfc2396.html

import logging
import queue
import re
import socket
import threading
import urllib.request
from urllib.parse import urlparse, urljoin, urlsplit, urlunsplit

import dflt_cfg
from .app_constant import *
from .urlparse import UrlNode


class AppURLopener ( urllib.request.FancyURLopener ):
    # This class is used as a mean to hack permission error due to use of urllib.
    version = "Mozilla/5.0"


class Crawler:
    """
    This class crawls every url of the user configured domain and build a tree hierarchy of UrlNode linking domain urls
    """
    def __init__ ( self ):
        self.logger = logging.getLogger ( __name__ )

        # this is used by parse threads to get a lock over get_create_urlnode function to ensure \
        # that only one urlnode gets created per unique url.
        self.mutex = threading.Lock ( )

        # num of parse threads
        self.NUM_PARSE_THREADS = dflt_cfg.DFLT_CFG[NUM_THREADS]

        # parse_th_list is actually redundant because as per the design of the application - parse threads \
        # always terminate. Keeping it for possible future enhancement.
        self.parse_th_list = [ ]

        # it contains references to urlnode objects for every url. It is used as a way to avoid \
        # creating dup urlnode for the same url. Format is: {url_str: urlnode_obj)
        self.url_instance = dict()

        # stores domain name of website (str)
        self.domain_name = self.get_simple_url ( self.get_domain_name ( dflt_cfg.DFLT_CFG[DOMAIN] ) )

        # this will be used to determine whether any discovered link belongs to same domain or not
        self.host = urlparse ( self.domain_name ).netloc

        # contains already visited url nodes (Object of UrlNode each)
        # it will be thread safe as all the threads will only add into it.
        self.visited_urlnodes = set ( )

        # contains currently discovered url nodes (UrlNode each), which will be consumed by parse threads.\
        # Queue is thread safe thanks to GIL.
        self.new_urlnodes_queue = queue.Queue ( )

        # it holds the root of urlNodes tree hierarchy
        self.urlnode_parse_root = None

    def start_url_parsing( self ):
        """
        Setup system proxy and initialize new_urls_queue with domain_name. Then it creates and starts urlparse threads.
        :return:
        """
        # setting system proxies
        self.config_urllib_proxy ( )

        # initializing url parse tree object (it holds the root of all urlNodes tree nodes; aka domain urlnode root)
        self.urlnode_parse_root = self.get_create_urlnode ( self.domain_name )

        # initialize new_urls_queue with domain_name urlnode instance
        self.insert_urlnodes_into_new_urls_queue ( self.urlnode_parse_root )

        # if num threads = 0 then do not create any thread and so directly call parse_site_urls
        if not self.NUM_PARSE_THREADS:
            self.parse_site_urls()
            return

        # creating and starting parse threads
        for _ in range ( self.NUM_PARSE_THREADS ):
            th = threading.Thread ( target=self.parse_site_urls )
            th.setDaemon ( daemonic=False )
            self.parse_th_list.append ( th )
            th.start ( )

    def release_urlparse_resources( self ):
        """
        Waits for and gracefully releases resources held by urlparse threads and return root urlnode of UrlTree.
        :return: the root of UrlNode tree hierarchy (an instance of UrlNode)
        """
        # if NUM_PARSE_THREADS = 0, then this function will not do anything
        for i in range ( self.NUM_PARSE_THREADS ):
            self.parse_th_list[i].join( )

        return self.urlnode_parse_root

    def parse_site_urls ( self ):
        """
        Used by threads to parse site urls. A thread fetches a urlnode instance from self.new_urlnodes_queue (if it can't fetch \
        a urlnode within user specified timeout seconds, then it exits). If this urlnode has already been visited, then it does \
        nothing and goes into next loop and redo the same operation.

        However, if the fetched urlnode has not been earlier visited, then first it adds this urlnode into self.visited_urlnodes \
        and find all urlnodes of the child urls of the current url (urlnode.url). All the child urlnodes are linked as \
        the children of urlnode of current url and all the child urlnodes that have not been visited earlier are added \
        into self.new_urlnodes_queue.
        :return:
        """
        while True:
            new_url_node = self.fetch_urlnode_from_new_urls_queue ( )

            # thread exits now if new_url_node is None (timeout has been expired!)
            if not new_url_node: break

            # attempting to add new_url_node into self.visited_urlnodes
            # if new_url_node is added into visited_urlnodes, returns True  else False (False means already existing)
            is_visited_urlnodes_updated = self.update_visited_urlnodes_if_newurlnode ( new_url_node )

            # it is a new node that has not been visited previously and has been added to self.visited_urlnodes
            if is_visited_urlnodes_updated:
                new_url = new_url_node.url  # str
                valid_page_child_urlnodes = self.find_valid_urlchildnodes_in_urlpage ( new_url )

                if valid_page_child_urlnodes:
                    # update the children of new_url_node and also put them into self.new_urlnodes_queue
                    for child_urlnode in valid_page_child_urlnodes:
                        new_url_node.child_urls.add ( child_urlnode )
                        self.insert_urlnodes_into_new_urls_queue ( child_urlnode )

    def find_valid_urlchildnodes_in_urlpage ( self, url ):
        """
        Finds all the valid urls listed on the url web page and creates urlnodes for those child urls (only those child urlnodes \
        which have not been created earlier) but returns all the child urlnodes for this url.
        :param url: str
        :return: a set which contains instances of valid child UrlNodes for given url
        """
        # contains urlnode instances (using set to avoid dup)
        found_valid_urlnodes = set ( )

        try:
            # response = urllib.request.urlopen ( url, timeout=cfg.CFG[TIMEOUT] )
            # Because of mod_security or some similar server security feature, server can \
            # easily block urllib.request.urlopen(),  as it is based on the user agent.
            # Hack: https://stackoverflow.com/a/31758803/4336040
            opener = AppURLopener ( )
            response = opener.open ( url )

        # Handling errors: https://stackoverflow.com/questions/8763451/how-to-handle-urllibs-timeout-in-python-3
        except (urllib.error.HTTPError, socket.timeout, urllib.error.URLError,) as err:
            self.logger.error ( "URL {0} cannot be open. Error: {1}".format ( url, err ) )
            return found_valid_urlnodes

        except Exception as err:
            self.logger.error ( "URL {0} cannot be open. Error: {1}".format ( url, err ) )
            return found_valid_urlnodes

        if response.getcode() != 200: # if response status is not Ok (e.g; asked url is dead or broken)
            self.logger.error ( "URL {0} cannot be open. Response code: {1}".format ( url, response.getcode() ) )
            return found_valid_urlnodes

        html_page = str ( response.read ( ) )
        pattern = '<a [^>]*href=[\'|"](.*?)[\'"].*?>'

        # list of child urls (content type: str)
        found_all_urls = re.findall ( pattern, html_page )

        # adding all the valid links in found_all_links into found_valid_urlnodes as urlnode
        for link in found_all_urls:
            url_node = self.get_acceptable_urlnode ( link )
            if url_node:  # this urlnode is acceptable
                found_valid_urlnodes.add ( url_node )

        return found_valid_urlnodes

    @staticmethod
    def config_urllib_proxy ( ):
        """
        Configuring system proxy for the application.
        :return:
        """

        # we need auth otherwise reported error we faced was:
        # urllib.error.URLError: <urlopen error [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed (_ssl.c:645)>
        # Solution: https://stackoverflow.com/a/36214206/4336040
        # Another possible approach (Didn't explore though): https://docs.python.org/3/library/ssl.html#ssl.create_default_context
        authinfo = urllib.request.HTTPBasicAuthHandler ( )

        # Reference: https://docs.python.org/3/library/urllib.request.html#examples
        proxy_support = urllib.request.ProxyHandler ( dflt_cfg.DFLT_CFG.get ( SYSTEM_PROXY ) )

        # build a new opener that adds authentication and caching FTP handlers
        opener = urllib.request.build_opener ( proxy_support, authinfo )

        # installing opening globally so that it will be used everywhere with urlrequest
        urllib.request.install_opener ( opener )

    def update_visited_urlnodes_if_newurlnode ( self, new_url_node ):
        """
        If a new visited urlnode is already in visited_urls set then return False and exit. \
        Otherwise insert new_url_node into visited_urls and return True
        :param new_url_node: object of UrlNode
        :return: bool
        """
        if self.is_url_already_visited ( new_url_node ): return False

        # insert into visited_urls
        self.visited_urlnodes.add ( new_url_node )
        return True

    def insert_urlnodes_into_new_urls_queue ( self, url_node ):
        """
        Put a new discovered url_node into new_urls_queue if it has never been visited.
        :param url_node: an instance of UrlNode
        :return:
        """
        # again checking as if another thread has already processed this url_node, then just return.
        if self.is_url_already_visited ( url_node ): return

        # Updating the full url of url_node by constructing a full (“absolute”) URL by combining \
        # a “base URL” (base) with another URL (url).
        # Reference: https://docs.python.org/2/library/urlparse.html#urlparse.urljoin
        url_node.url = urljoin ( self.domain_name, url_node.url )

        # no need to specify timeout as new_urls_queue can contain infinite urls
        self.new_urlnodes_queue.put ( item=url_node, block=True )

    def fetch_urlnode_from_new_urls_queue ( self ):
        """
        Removes and returns an UrlNode from new_urlnodes_queue. \
        If an url node can't be fetched within timeout, it sends None to thread (consequently the \
        calling thread will use it as an exit point and terminate itself). Otherwise this function \
        returns the retrieved urlnode to the calling thread.
        :return: instance of UrlNode (object) / None
        """
        try:
            # means all is okay signal for thread
            return self.new_urlnodes_queue.get ( block=True, timeout=dflt_cfg.DFLT_CFG.get ( TIMEOUT ) )
        except queue.Empty:
            # signal for thread to exit
            return None

    @staticmethod
    def get_simple_url ( url ):
        """
        To ensure that url follows RFC 2396, this function returns a slightly different
        (Parameters for last path element), but equivalent URL, if the URL that was parsed
        originally had unnecessary delimiters (for example, a ? with an empty query;
        the RFC states that these are equivalent).

        Reference: https://docs.python.org/2/library/urlparse.html#urlparse.urlunsplit
        :param url: str
        :return: rfc 2396 confirmed equivalent url (str)
        """
        # Reference: https://tools.ietf.org/html/rfc2396.html#appendix-G.4
        # ----------------------------------------------------------------
        #     Extensive testing of current client applications demonstrated that the majority of deployed \
        #     systems do not use the ";" character to indicate trailing parameter information, and that \
        #     the presence of a semicolon in a path segment does not affect the relative parsing of that \
        #     segment. Therefore, parameters have been removed as a separate component and may now appear \
        #     in any path segment. Their influence has been removed from the algorithm for resolving a \
        #     relative URI reference.

        # Other References: https://stackoverflow.com/questions/5472160/which-should-i-be-using-urlparse-or-urlsplit?utm_medium=organic&utm_source=google_rich_qa&utm_campaign=google_rich_qa
        #                   https://pymotw.com/3/urllib.parse/#parsing

        # first strip off the url which contains #, as # is used it go to different section of the SAME page.
        if '#' in url:
            url = url[ :url.find ( '#' ) ]

        scheme, netloc, path, query, fragment = urlsplit ( url )
        return urlunsplit ( (scheme, netloc, path, query, fragment) )

    def get_acceptable_urlnode ( self, url ):
        """
        Returns a urlnode (creates one if it has never been visited earlier) for an url if it satisfies \
        these three conditions: \
            1. url belongs to either http or https scheme, \
            2. url belongs to the same domain, and \
            3. url has never been visited.

        Otherwise, this function returns None.

        :param url: str
        :return: an instance of UrlNode / None
        """
        url = self.get_simple_url(url)

        # If url scheme is not http or https, reject this url
        if not self.is_http_url ( url ): return None

        # If url is from external domain, reject this url
        if not self.is_internal_url ( url ): return None

        urlnode = self.get_create_urlnode(url)

        # If url is already visited, reject this url
        if self.is_url_already_visited ( urlnode ): return None

        return urlnode

    def get_create_urlnode( self, url ):
        """
        For threads , this function mutually exclusively creates UrlNode for an url. This function is \
        thread safe as a mean to ensure that dup UrlNodes do not get created for the same url.
        :param url: str
        :return: an instance of UrlNode
        """
        url = self.get_simple_url(url)

        self.mutex.acquire ( )
        # here only one thread at a time will be there.
        # we are ensuring that when two/more threads create only instance of urlnode for the same url
        urlnode = self.url_instance.get ( url )
        if not urlnode:
            urlnode = UrlNode ( url )
            self.url_instance[ url ] = urlnode

        self.mutex.release( )

        return urlnode

    @staticmethod
    def is_http_url ( url ):
        """
        If url is not empty str and belongs to either http or https scheme then return True; else False
        :param url: str
        :return: bool
        """
        # urlsplit parses a URL into 5 components: <scheme>://<netloc>/<path>?<query>#<fragment>
        # and it returns a 5-tuple: (scheme, netloc, path, query, fragment).
        scheme, _, _, _, _ = urlsplit ( url )

        if url and scheme in ('http', 'https', ''):
            return True

        return False

    def is_internal_url ( self, url ):
        """
        If url belongs to same domain returns True; else False
        :param url: str
        :return: bool
        """
        host = urlparse ( url ).netloc
        if host == self.host or host == '':
            return True

        return False

    def is_url_already_visited ( self, urlnode ):
        """
        If this urlnode has already been visited then return True; else return False
        :param urlnode: an instance of UrlNode
        :return: bool
        """
        if urlnode in self.visited_urlnodes: return True
        return False

    @staticmethod
    def get_domain_name ( domain_name ):
        """
        In case the home address of website is not provided, it will give the domain name

        Example: If passed domain_name = 'http://stackoverflow.com/questions/1234567/blah-blah-blah-blah'
                 Then this function will return 'http://stackoverflow.com/'

        Reference: https://stackoverflow.com/questions/9626535/get-domain-name-from-url?utm_medium=organic&utm_source=google_rich_qa&utm_campaign=google_rich_qa
        :param domain_name: str
        :return: real domain name (str)
        """
        parsed_uri = urlparse ( domain_name )
        domain = '{uri.scheme}://{uri.netloc}/'.format ( uri=parsed_uri )

        return domain

