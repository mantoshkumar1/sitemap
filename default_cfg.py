from webcrawler.app_constant import *

DFLT_CFG = {
    OUTPUT_DIR: "./outputs",

    # If domain is not known to be slow responsive, increase this value
    TIMEOUT: 10,

    # If you need to use a proxy, assign a dictionary (e.g; using proxies argument) mapping protocol \
    # or protocol and host to the URL of the proxy to be used on each Request using SYSTEM_PROXY configuration. \
    # Otherwise, configure it to a None for auto detectable proxies from the environment variables.
    #
    # To disable auto detected proxy pass an empty dictionary. For example, in order to test scripts with \
    # a localhost server, you need to prevent urllib from using the proxy and thus requires {}.
    #
    # For detailed info, please visit https://docs.python.org/3.5/howto/urllib2.html#proxies
    # proxies = {
    #     'http': 'http://10.10.1.10:3128',
    #     'https': 'http://10.10.1.10:1080',
    # }
    SYSTEM_PROXY: None,
}
