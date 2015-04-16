# coding: UTF-8
from django.contrib import admin
from polls.models import User

class UserAdmin(admin.ModelAdmin):
  # 表示レイアウト
  fieldsets = [
    (None, { 'fields': ['user_id'] }),
    ('Date information', { 'fields': ['pub_date'], 'classes': ['collapse'] }),
  ]
  # 表示項目
  list_display = ('user_id', 'access_token')
  # フィルタ項目
  list_filter = ['pub_date']
  # 検索項目
  search_fields = ['user_id']
  # 日付でフィルタリング
  date_hierarchy = 'pub_date'

admin.site.register(User, UserAdmin)