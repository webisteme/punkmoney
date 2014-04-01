import os
import sys

path = '/home/punkmoney/'
if path not in sys.path:
    sys.path.append(path)

os.environ['DJANGO_SETTINGS_MODULE'] = 'punkmoney.settings'

import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()