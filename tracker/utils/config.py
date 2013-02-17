# -*- coding: utf-8 -*-
"""

PunkMoney 0.2 :: Configuration File

"""

# COMMUNITY
'''
Currency hashtag, name of trustlist and seed_user to crawl from
'''

HASHTAG = '#testmoney'
ALT_HASHTAG = '#tmny'


# TWITTER API CREDENTIALS
'''
Create an app at http://developers.twitter.com. 
Ensure it has read/write access
'''
TW_CONSUMER_KEY = 'jKrDL2A1g6VJJXgtAkzRuA'
TW_CONSUMER_SECRET = 'I94MrSx5wBn3PfLSFJERGn7BEJMvNct0sEoxv0dYg'

TW_ACCESS_KEY = '398204399-y7KpHT4L03HexOuq3eIpuysX0uBuzHGVoBRpY0SM'
TW_ACCESS_SECRET = 'uitAR5ZljqTdwBFkBHDEAnxgEect030c7wXnYLyY'


# MYSQL DATABASE
'''
MySQL database credentials. Socket locations can vary depending on the system.
'''
MYSQL_HOST = 'localhost'
MYSQL_USER = 'root'
MYSQL_DATABASE = 'punkmoney3'
MYSQL_PASSWORD = '12673013'
MYSQL_SOCKET = '/tmp/mysql.sock'

# LOG PATH
LOG_PATH = '/Users/Eli/Documents/punkmoney0.2/tracker/logs/punkmoney.log'


# SETTINGS
''' 
Set tweet to true to tweet syntax errors via the main Twitter account.
Set debug to true to log debug messages
'''

SETTINGS = {
    'tweet' : False,
    'debug' : True,
    'twipm' : False,
}