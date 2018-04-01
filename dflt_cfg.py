from webcrawler.app_constant import *

DFLT_CFG = {
    # Domain for which sitemap will be generated (it will get updated with user argument)
    DOMAIN: None,

    # Number of concurrent threads performing domain crawling. (must be >=0)
    NUM_THREADS : 4,

    # Location where sitemap will be stored
    OUTPUT_PATH: "./output/output.txt",

    # Application timeout in seconds (must be >=0)
    TIMEOUT: 10,

    # system proxy if applicable (Please read README file)
    SYSTEM_PROXY: None,

    # Set the level of logs which will be collected by this application. (0<=LOG_LEVEL<=5)
    LOG_LEVEL : 2
}
