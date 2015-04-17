# -*- coding: utf-8 -*-
import os
import site
import sys

# virtualenvのパッケージパス
site.addsitedir("/home/ec2-user/ENV/lib/python2.7/site-packages")

sys.path.append('/var/www/cgi-bin/EN_Markdown')

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "evernote_oauth_sample.settings")

# virtualenvの実行コードのパス
activate_env = os.path.expanduser("/home/ec2-user/ENV/bin/activate_this.py")
execfile(activate_env, dict(__file__=activate_env))

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()