# -*- coding: utf-8 -*-
from django.conf.urls import patterns, url
from cms import views

urlpatterns = patterns('',
    # 書籍
    url(r'^user/$', views.user_list, name='user_list_all'),   # 一覧
    url(r'^user/(?P<user_id>\d+)/$', views.user_list, name='user_list'),   # 一覧
    url(r'^user/add/$', views.user_edit, name='user_edit'),  # 登録
    url(r'^user/mod/(?P<user_id>\d+)/$', views.user_edit, name='user_mod'),  # 修正
    url(r'^user/del/(?P<user_id>\d+)/$', views.user_del, name='user_del'),   # 削除
)