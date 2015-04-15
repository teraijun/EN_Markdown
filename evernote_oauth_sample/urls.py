from django.conf.urls import patterns, url, include
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns(
    '',
    url(r"^$", "oauth.views.index", name="evernote_index"),
    url(r"^auth/$", "oauth.views.auth", name="evernote_auth"),
    url(r"^login/$", "oauth.views.login", name="evernote_login"),
    url(r"^info/$", "oauth.views.get_info", name="evernote_info"),
    url(r"^reset/$", "oauth.views.reset", name="evernote_auth_reset"),
    url(r"^note/$", "oauth.views.note", name="evernote_note"),
    url(r'^admin/', include(admin.site.urls)),
)
