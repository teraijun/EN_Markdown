# -*- coding: utf-8 -*-
from django.db import models

# Create your models here.
class User(models.Model):
    '''書籍'''
    user_id = models.CharField(u'user_id', max_length=255)
    access_token = models.CharField(u'access_token', max_length=255, blank=True)

    def __unicode__(self):    # Python2: def __unicode__(self):
        return self.user_id
