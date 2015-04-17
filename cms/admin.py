# -*- coding: utf-8 -*-
from django.contrib import admin
from cms.models import User

class UserAdmin(admin.ModelAdmin):
    list_display = ('id', 'user_id', 'access_token')  # 一覧に出したい項目
    list_display_links = ('id', 'access_token',)  # 修正リンクでクリックできる項目
admin.site.register(User, UserAdmin)