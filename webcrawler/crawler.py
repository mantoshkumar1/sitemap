# https://pymotw.com/3/urllib.parse/#parsing
# Uniform Resource Identifiers (URI): Generic Syntax: https://tools.ietf.org/html/rfc2396.html

import logging
import os
import queue
import re
import socket
import threading
import urllib.request
from urllib.parse import urlparse, urljoin, urlsplit, urlunsplit

import default_cfg
from .app_constant import *
from .urlparse import UrlNode


class AppURLopener ( urllib.request.FancyURLopener ):
    version = "Mozilla/5.0"


class Crawler:
    def __init__ ( self, domain_name, output_file_name, num_threads ):
        """
        :param domain_name: Host or domain name of a website (todo: str?)
        :param output_file_name: Plaintext file name where output will be stored (todo: str ?)
        :param num_threads: Number of web crawling threads (int)
        """
        self.logger = logging.getLogger ( __name__ )

        self.url_instance = dict() # {url_str: urlnode obj)

        # setting system proxies
        self.config_urllib_proxy ( )

        self.host = urlparse ( domain_name ).netloc

        # stores domain name of website (str)
        # self.domain_name = self.get_simple_url ( self.get_domain_name ( domain_name ) )
        self.domain_name = self.get_simple_url ( domain_name )

        # stores system path of output file (str)
        self.output_file_path = self.set_output_file_path ( output_file_name )

        # contains already visited url nodes (Object of UrlNode each)
        # it will be thread safe as all the threads will only add into it.
        self.visited_urlnodes = set ( )

        # contains currently discovered url nodes (UrlNode each)
        # Queue is thread safe thanks to GIL.
        self.new_urlnodes_queue = queue.Queue ( )

        # initializing url parse tree object (this will hold the root of all the urlNodes tree nodes)
        self.urlnode_parse_root = self.get_create_urlnode(self.domain_name)

        # initialize new_urls_queue with domain_name
        self.insert_urlnodes_into_new_urls_queue ( self.get_create_urlnode(self.domain_name) )

        # initializing threads
        self.num_threads = num_threads

        # th_list is actually redundant as per the design of the application as threads always terminate.
        self.th_list = [ ]

        #self.parse_site_urls ( )

        self.create_start_urlparse_threads()

        self.set_log_level ( 2 )


    def create_start_urlparse_threads ( self ):
        for _ in range ( self.num_threads ):
            th = threading.Thread ( target=self.parse_site_urls )
            th.setDaemon ( daemonic=False )
            self.th_list.append ( th )
            th.start ( )

    def wait_for_urlparse_threads( self ):
        for i in range ( self.num_threads ):
            self.th_list[i].join( )

    def parse_site_urls ( self ):
        """
        Used by threads to parse urls. It fetches a urlnode instance from new_urlnodes_queue and gets all the children \
        urls listed in its webpage and if the fetched url has not been visited previously then it adds those children \
        urls (urlnodes) into the new_urlnodes_queue and also adds fetched url (urlnode) into visited_urlnodes.

        However, if the fetched url (urlnode) has been visited earlier, then it just goes into loop.
        :return:
        """
        while True:
            new_url_node = self.fetch_urlnode_from_new_urls_queue ( )

            # thread exits now if new_url_node is None (timeout has been expired!)
            if not new_url_node: break

            # attempting to add new_url_node into self.visited_urlnodes
            # if new_url_node is added into visited_urlnodes, returns True  else False (has already been existing)
            is_visited_urlnodes_updated = self.update_visited_urlnodes_if_newurlnode ( new_url_node )

            # it is a new node that has not been visited previously and has been added to self.visited_urlnodes
            if is_visited_urlnodes_updated:
                new_url = new_url_node.url  # str
                valid_page_child_urlnodes = self.find_valid_links_in_urlpage ( new_url )

                if valid_page_child_urlnodes:
                    # update the children of new_url_node and also put them into self.new_urlnodes_queue
                    for child_urlnode in valid_page_child_urlnodes:
                        new_url_node.child_urls.add ( child_urlnode )
                        self.insert_urlnodes_into_new_urls_queue ( child_urlnode )

    def find_valid_links_in_urlpage ( self, url ):
        """
        Finds all the valid urls listed on the url web page.
        :param url: str
        :return: a List which contains instances of valid UrlNodes.
        """
        url = self.get_simple_url(url)
        # contains urlnode instances (using set to avoid dup)
        found_valid_urlnodes = set ( )

        try:
            # response = urllib.request.urlopen ( url, timeout=default_cfg.DFLT_CFG[TIMEOUT] )
            # Because of mod_security or some similar server security feature, server can \
            # easily block urllib.request.urlopen(),  as it based on the user agent.
            # Hack: https://stackoverflow.com/a/31758803/4336040
            opener = AppURLopener ( )
            response = opener.open ( url )

        # Handling errors: https://stackoverflow.com/questions/8763451/how-to-handle-urllibs-timeout-in-python-3
        except (urllib.error.HTTPError, socket.timeout, urllib.error.URLError,) as err:
            self.logger.error ( "URL {0} cannot be open. Error: {1}".format ( url, err ) )
            return found_valid_urlnodes

        except:
            self.logger.error ( "Thread exiting: URL {0} cannot be open".format(url) )
            import sys
            sys.exit ( )

        page = str ( response.read ( ) )
        pattern = '<a [^>]*href=[\'|"](.*?)[\'"].*?>'

        # list of strings
        found_all_urls = re.findall ( pattern, page )

        # adding all the valid links in found_all_links into found_valid_urlnodes as urlnode
        for link in found_all_urls:
            url_node = self.get_acceptable_urlnode ( link )
            if url_node:  # this urlnode is acceptable
                url_node.url = self.get_simple_url ( link )
                found_valid_urlnodes.add ( url_node )

        return found_valid_urlnodes

    @staticmethod
    def config_urllib_proxy ( ):

        # we need auth otherwise reported error we faced was:
        # urllib.error.URLError: <urlopen error [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed (_ssl.c:645)>
        # Solution: https://stackoverflow.com/a/36214206/4336040
        # Another possible approach (Didn't explore though): https://docs.python.org/3/library/ssl.html#ssl.create_default_context
        authinfo = urllib.request.HTTPBasicAuthHandler ( )

        # Reference: https://docs.python.org/3/library/urllib.request.html#examples
        proxy_support = urllib.request.ProxyHandler ( default_cfg.DFLT_CFG.get ( SYSTEM_PROXY ) )

        # build a new opener that adds authentication and caching FTP handlers
        opener = urllib.request.build_opener ( proxy_support, authinfo )

        # installing opening globally so that it will be used everywhere with urlrequest
        urllib.request.install_opener ( opener )

    def update_visited_urlnodes_if_newurlnode ( self, new_url_node ):
        """
        If a new visited urlnode is already in visited_urls set then do nothing, else insert new_url_node into visited_urls.
        :param new_url_node: object of UrlNode
        :return:
        """
        # import pdb;pdb.set_trace()
        if self.is_url_already_visited ( new_url_node ): return False

        # insert into visited_urls
        self.visited_urlnodes.add ( new_url_node )
        return True

    def insert_urlnodes_into_new_urls_queue ( self, url_node ):
        """
        Put a new discovered url_node into new_urls_queue if it has already been not visited.
        :param url_node: str
        :return:
        """
        # again checking as if another thread has already processed this url_node, then just return.
        if self.is_url_already_visited ( url_node ): return False

        # Updating the full url of url_node by constructing a full (“absolute”) URL by combining \
        # a “base URL” (base) with another URL (url).
        # Reference: https://docs.python.org/2/library/urlparse.html#urlparse.urljoin
        url_node.url = urljoin ( self.domain_name, url_node.url )

        # no need to specify timeout as new_urls_queue can contain infinite urls
        self.new_urlnodes_queue.put ( item=url_node, block=True )
        return True

    def fetch_urlnode_from_new_urls_queue ( self ):
        """
        Removes and returns an URL from new_urls_queue.
        If an url node can't be fetched within timeout, it sends None to thread (consequently the
        calling thread will used it as an exit point and terminate itself). Otherwise this function
        returns the retrieved url node to the calling thread.
        :return: instance of UrlNode (object) or None
        """
        try:
            # means all is okay signal for thread
            return self.new_urlnodes_queue.get ( block=True, timeout=default_cfg.DFLT_CFG.get ( TIMEOUT ) )
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

        :param url: str
        :return: an instance of UrlNode
        """
        # If url scheme is not http or https, reject this url
        if not self.is_http_url ( url ): return None

        # If url is from external domain, reject this url
        if not self.is_internal_url ( url ): return None

        urlnode = self.get_create_urlnode(url)

        # If url is already visited, reject this url
        if self.is_url_already_visited ( urlnode ): return None

        return urlnode

    def get_create_urlnode( self, url ):
        url = self.get_simple_url(url)
        urlnode = self.url_instance.get ( url )
        if not urlnode:
            urlnode = UrlNode ( url )
            self.url_instance[ url ] = urlnode
        return urlnode

    @staticmethod
    def is_http_url ( url ):
        """
        If url is not empty str and belongs to either http or https scheme then return True; else False
        :param url: str
        :return:
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
        :return:
        """
        host = urlparse ( url ).netloc
        if host == self.host or host == '':
            return True

        return False

    def is_url_already_visited ( self, urlnode ):
        """
        If this urlnode is already visited then return True; else return False
        :param urlnode: an instance of UrlNode
        :return:
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

    def write_output_file ( self, url_txt ):
        """
        Write url into the output file
        :param url_txt: txt formated url tree
        :return:
        """
        with open ( file=self.output_file_path, mode='w' ) as fd:
            fd.write ( url_txt )

    def set_output_file_path ( self, output_file_name ):
        """
        Set output file path to self.output_file_path
        :param output_file_name: Name of output file path received from cmd line args (str)
        #todo: verify output_file_name must be received as str only ?
        :return: System path of the output file (str)
        """
        output_file_path = default_cfg.DFLT_CFG[ OUTPUT_DIR ] + '/' + output_file_name

        # if output file exists, then delete it
        if os.path.isfile ( output_file_path ):
            os.remove ( output_file_path )

        return output_file_path

    def set_log_level ( self, user_log_level=2 ):
        """
        This function set the log level of this application using the log level provided by
        user as args through cmdline. if the cmdline provided log level is invalid, then
        by default, application chooses INFO level logging
        :param user_log_level: log level provided by user as args through cmd line (int)
        :return:
        """
        # todo: take user_log_level as optional args from command prompt
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
        if not mapped_log_level:
            mapped_log_level = std_logging_levels[ 2 ]

        logging.getLogger ( ).setLevel ( mapped_log_level )

        self.logger.info ( "test debug" )
