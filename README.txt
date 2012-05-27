'''

PunkMoney 0.25 
by Eli Gothill (@webisteme)

www.punkmoney.org
www.webisteme.com/blog

'''

ABOUT

#PunkMoney is a set of natual language protocols which enable a gift economy on Twitter. PunkMoney 0.25 is the second iteration of the #PunkMoney tracker for finding, interpreting and recording #PunkMoney statements.

To find out more about #PunkMoney, visit http://www.punkmoney.org


LICENSE

This software is released under the MIT Open Source License (MIT). Please see LICENSE.txt.


DEPENDENCIES

Python 2.6+
Django 1.3
MySQL Server 5.5+
Unix environment (with cron)

Web dependencies:

Blueprint CSS (included)
d3 Javascript Library (included)

Python dependencies:

Tweepy (https://github.com/tweepy/tweepy)
Dateutils (http://labix.org/python-dateutil)
MySQL for Python (http://sourceforge.net/projects/mysql-python/)


INSTALLATION

PunkMoney has two parts: a tracker for finding, interpreting and storing #PunkMoney statements and gestures from the Twitter API, and a web interface for displaying them. Both parts need to be configured separately, in this order:

Web interface (Django):

(1) Create a MySQL database (UTF-8 charset):

CREATE DATABASE punkmoney CHARACTER SET utf8 COLLATE utf8_general_ci;

(2) Create your settings in /web/settings_template.py, then rename to settings.py. Be sure to add a template path (an absolute path to the template directory,) and your MySQL database credentials.
(3) Run python manage.py syncdb to create the necessary tables
(4) Run python manage.py runserver to check it's set up correctly.
(5) Deploy Django (this step varies depending on your system. For apache, use django.wsgi and create a corresponding sites-available URL record.)

(For help deploying Django on your system, see https://docs.djangoproject.com/en/dev/howto/deployment/)

Tracker (Python):

(1) Create your settings in /tracker/utils/config_template.py, then rename to config.py.
(2) Run python Tracker.py to test it's working properly (this will pull in any recent tweets from the Twitter API)
(3) Make sure Tracker.py, /utils/trustlist.py and /utils/redemptions.py are executable (chmod 755 filename.py)
(4) Type crontab -e to open cron. Schedule the following tasks: 
    - Tracker.py to run once per minute
    - utils/trustlist.py to run once per hour
    - utils/redemptions.py to run once per hour
Check the logs and/or database to ensure the cron tasks are running properly


NOTES

The #PunkMoney wiki is located at http://wiki.punkmoney.org and contains the development roadmap and details on the project.

For testing purposes, please use your own hasthag rather than #punkmoney or #pmny -- this is to keep test data out of the main tracker at www.punkmoney.org - thanks.


SUPPORT

Contact egothill[@]gmail[.]com or @webisteme for help, feedback or bug reports.




