# -*- coding: utf-8 -*-
from django.forms import ModelForm
from cms.models import User

class UserForm(ModelForm):
    '''Form of User'''
    class Meta:
        model = User
        fields = ('user_id', 'access_token')