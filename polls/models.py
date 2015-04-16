# coding: UTF-8
from django.db import models

#
# 
#User
#
class User(models.Model):
  user_id = models.CharField(u'user_id', max_length=200)
  access_token = models.CharField(u'access_token', max_length=200, blank=True)
  pub_date = models.DateTimeField('date published')
  
  def __unicode__(self):
    return self.user_id
