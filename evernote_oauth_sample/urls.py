from django.conf.urls import patterns, url


urlpatterns = patterns(
    'oauth.views',
    url(r"^$", "index", name="evernote_index"),
    url(r"^auth/$", "auth", name="evernote_auth"),
    url(r"^login/$", "login", name="evernote_login"),
    url(r"^info/$", "get_info", name="evernote_info"),
    url(r"^reset/$", "reset", name="evernote_auth_reset"),
    url(r"^note/$", "note", name="evernote_note"),
)
