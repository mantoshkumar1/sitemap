# Domain Crawler - Domain Mapping
This application is a web crawler which crawls all the pages within a particular domain and produces a sitemap
(only internal URLs) for that domain and finds the links between its web pages, and finally stores the whole sitemap of the domain
the local hard disk. The application also lists all the broken and dead URLs within that domain and stores them on local hard disk.

## How to install the application software requirements
<code>$ cd sitemap</code><br>
Choose only one of the below option (Read **_setuptools Note_** below):
* If user wants to install and use the required packages:<br>
<code>$ sudo python setup.py install</code>
* Instead, if user does not want to install the required packages, however, still would like to just use them, then execute:<br>
<code>$ sudo python setup.py develop</code>

This application has been developed and tested on Ubuntu 16.04 LTS OS using Python 3.5.2. For other OS platforms, few instructions might need to be adapted.

**setuptools Note**: If _setuptools_ is not installed on user's system, please execute these two instructions first, as 
_setuptools_ package is the prerequisite for _setup.py_ to work:<br>
<code>$ sudo apt install python-pip</code><br>
<code>$ sudo pip install setuptools</code>

## How to run the application
<code>$ cd sitemap</code><br>
<code>$ export PYTHONPATH=$PWD</code><br>
<code>$ python generate_sitemap.py -nt 8 -l 4 -t 5 -f monzo_sitemap.txt -d https://monzo.com/</code>

###### Output of application:
```text
Sitemap for https://monzo.com/ is written in ./output/monzo_sitemap.txt.
Logs (Broken or dead URLs along with application logs) for domain https://monzo.com/ are available in ./logs directory.
-------------------------------------------------------------------
<<Thank you for using Domain Crawler - Domain Mapping application>>
-------------------------------------------------------------------
```

###### Help on command-line options and arguments of the application:
<code>$ python generate_sitemap.py -h</code><br>
```
usage: generate_sitemap.py [-h] [-nt N] [-l L] [-t T] [-f File_Name] -d Domain

Domain Crawler - Domain Mapping

optional arguments (For an invalid arg value, default value will be picked up):
  -h, --help            show this help message and exit
  -nt N, --nthread N    number of threads (N>=0: default=4)
  -l L, --log L         log level (0<=L<=5: default=2)
  -t T, --timeout T     timeout in seconds (T>=0: default=10)
  -f File_Name, --file File_Name
                        name of the output file (default=output.txt): stored in output directory
                        
required arguments:
  -d Domain, --domain Domain
                        name of the domain
```

**Note 1**: The sitemap result and logs get stored in **_./output_** and **_./logs_** directory respectively. The log files contains
broken or dead links within the domain along with application logs.<br>

**Note 2**:  Ideally the user should provide absolute web address for a _Domain_. In case the provided value is different than absolute
domain address, then application calculates the absolute domain address on its own using provided values.<br>
Example: If user provides _Domain_ = 'https://monzo.com/about/', then the application will still build sitemap for 'https://monzo.com/' only.

**Note 3**: By default, the application enforces default values for optional arguments. However, the application supports flexibility
to change default values as per user's requisites. Please visit [Custom Default Configuration Settings](#custom-default-configuration-settings-for-advanced-users) 
subsection for changing default configuration settings.

# How to execute unit tests for the application
<code>$ cd sitemap</code><br>
<code>$ python -m unittest discover</code>

# How to produce code coverage report of the application
[*Only once:*] If _Coverage_ package is not installed on user's system, please install this package
 [(version 4.5.1 with C extension)](http://coverage.readthedocs.io/en/coverage-4.5.1/index.html) in the local system
  by executing the following command:<br>
<code>$ pip install -U coverage</code><br>

<code>$ cd sitemap</code><br>
<code>$ sh eval_code_coverage.sh</code>

**Note**: The produced code coverage report will get generated inside **_./documentation/coverage_html_report/_**. The
above executed shell script automatically opens the home HTML page (**_./documentation/coverage_html_report/index.html_**)
of application code coverage report.

## Custom Default Configuration Settings (For Advanced Users)
User can adjust the default configuration of this tool by modifying **dflt_cfg.py**. By default, each field is assigned a value.
For any invalid/absent optional command line argument values, default values stored in _dflt_cfg.py_ will automatically
get enforced for the application. This section details the explanation of each such field. <br>

* **NUM_THREADS**: Specifies number of threads that crawls the domain concurrently.    
    * Expected value: Non-negative integer
    * Default value: _4_
    
* **OUTPUT_PATH**: Specifies the file location where generated sitemap for a domain will get written.    
    * Expected value: A valid absolute/relative system path to a file in a string format. In case of relative path, it should 
    be relative to application home directory (./sitemap) only.
    * Default value: _"./output/output.txt"_
    
* **TIMEOUT**: Specifies the waiting time (seconds) before application terminates in case of an unresponsive domain.    
    * Expected value: Non-negative integer
    * Default value: _10_     
 
* **SYSTEM_PROXY**: Using a dictionary (e.g; proxies below), it specifies mapping protocol or protocol and host to the URL of 
the proxy to be used on each urlopen request. 

    If the user system is behind a proxy, assign a dictionary (e.g; using proxies argument) mapping protocol 
    or protocol and host to the URL of the proxy to be used on each urlopen request using SYSTEM_PROXY configuration.

    If the user system is not behind a proxy or user prefers urllib to auto-detect the proxies from the environment 
    variables, then please set it to None. Normally that’s a good thing, but there are occasions 
    when it may not be helpful (Reference: [Footnote 5](https://docs.python.org/3.5/howto/urllib2.html#id12)). 

    To disable auto detected proxy, please pass an empty dictionary. For example, in order to test scripts with a localhost server, 
    user might need to prevent urllib from using the proxy and thus requires {}.
    
    * Expected value: dictionary / None
    * Default value: _None_

    For detailed information, please visit [urllib Proxies Details](https://docs.python.org/3.5/howto/urllib2.html#proxies).<br>
    ```text
          proxies = {
                    'http': 'http://10.10.1.10:3128',
                    'https': 'http://10.10.1.10:1080',
          }
    ```
     
* **LOG_LEVEL**:  Specifies the log level of the application.
    * Expected value: 0 <= LOG_LEVEL <= 5 (0 is the lowest level log severity and 5 is the highest level log severity)
    * Default value: _2_
    
## Architecture for Domain Crawler - Domain Mapping
