from evernote.api.client import EvernoteClient
from evernote.api.client import Store
from evernote.edam.type.ttypes import (
    Note
)
import evernote.edam.type.ttypes as Types
import evernote.edam.error.ttypes as Errors
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response
from django.shortcuts import redirect
from django.http import HttpResponse
from django.middleware.csrf import get_token
from django.conf import settings
from django.core import serializers
from cms.models import User
import json
import Cookie
import os
import socket
import oauth2 as oauth
import urllib
import urlparse
import hashlib
import binascii
from PIL import Image
import io
import cStringIO

sandbox = True

if sandbox : 
    link_to_en = 'https://sandbox.evernote.com/Home.action'
else : 
    link_to_en = 'https://www.evernote.com/Home.action'

def get_evernote_client(token=None):
    if token:
        return EvernoteClient(token=token, sandbox=sandbox)
    else:
        return EvernoteClient(
            consumer_key=settings.EN_CONSUMER_KEY,
            consumer_secret=settings.EN_CONSUMER_SECRET,
            sandbox=sandbox
        )

def index(request):
    csrf_token = get_token(request)
    response = render_to_response('index.html')
    return response

def callback(request):
    client = get_evernote_client()
    if 'oauth_verifier' in request.GET:
        oauth_verifier = request.GET.get("oauth_verifier")
        access_token = client.get_access_token(
            request.COOKIES['oauth_token'],
            request.COOKIES['oauth_token_secret'],
            oauth_verifier
        )
        client = EvernoteClient(token=access_token)
        user_store = client.get_user_store()
        user = user_store.getUser()
        username = user.username
        shard_id = user.shardId
        privilege = user.privilege

#        request.session['shard_id'] = shard_id

        u = User(
            user_id=user.id,
            access_token=access_token)
        u.save()

    # Redirect the user to the Evernote authorization URL
    try:
        callbackUrl = request.COOKIES['_redirect_url']
    except Exception as e :
        callbackUrl = 'http://%s/' % (request.get_host())
    response = redirect(callbackUrl)
    response.set_cookie('access_token', access_token)
    response.delete_cookie('_redirect_url')
    return response

def login(request):
    if 'callback' in request.GET:
        callbackUrl = request.GET.get('callback').decode("utf-8")+'callback/'
    else :
        callbackUrl = 'http://www.nikkei.com/'
    client = get_evernote_client()
    request_token = client.get_request_token(callbackUrl)

    response = redirect(client.get_authorize_url(request_token))
    response.set_cookie('oauth_token', request_token['oauth_token'])
    response.set_cookie('oauth_token_secret', request_token['oauth_token_secret'])
    return response

def get_info(request):
    try:
        client = get_evernote_client(token=request.COOKIES['access_token'])
    except KeyError:
        return json_response_with_headers({
            'status': 'redirect',
            'redirect_url': '/login/',
            'home_url': link_to_en,
            'msg': 'Login to use'
        })

    note_store = client.get_note_store()
    notebooks = note_store.listNotebooks()

    user_store = client.get_user_store()
    user_info = user_store.getUser()

    notes = [];
    print notebooks
    if notebooks is not None:
        for note in notebooks:
            notes.append({
                'name': note.name,
                'guid': note.guid
            })
    return json_response_with_headers({
            'status': 'success',
            'redirect_url': '/logout/',
            'msg': 'Logout',
            'home_url': link_to_en,
            'notebooks': notes,
            'username': user_info.username
    })

def reset(request):
    return redirect('/')

def note(request):
    request.token = request.COOKIES['access_token']

    if 'title' in request.POST:
        title = request.POST['title'].encode("utf-8")
    if 'body' in request.POST:
        body = request.POST['body'].encode("utf-8")
    if 'files' in request.POST:
        resources = json.loads(request.POST["files"])
    else :
        resources = []
    if 'guid' in request.POST:
        guid = request.POST['guid']
    try:
        note = make_note(request, title, body, resources, guid)
        if note :
            return json_response_with_headers({
                'status': 'success',
                'note': note
            })
        else :
            return json_response_with_headers({
            'status': 'error',
            'msg': 'note is null'
        })
    except Exception as e:
        return json_response_with_headers({
            'status': 'error',
            'msg': 'parameter error',
            'title': title,
            'body': body,
            'resources': resources,
            'guid': guid,
            'access_token': request.token,
            'error': e.args
        })

def make_note(client, noteTitle, noteBody, resources=[], guid=''):
    ## Build body of note
    body = "<?xml version=\"1.0\" encoding=\"UTF-8\"?>"
    body += "<!DOCTYPE en-note SYSTEM \"http://xml.evernote.com/pub/enml2.dtd\">"
    body += "<en-note>%s" % noteBody

    ourNote = Note()
    ourNote.title = noteTitle

    if len(resources) > 0:
        ourNote.resources = []
        body += "<br />" * 2
        for res in resources:
            src = res['src']
            file = cStringIO.StringIO(urllib.urlopen(src).read())
            img = Image.open(file)
            # img = Image.open(file).resize((120,120))
            output = io.BytesIO()
            img.save(output, format='png')
            im = output.getvalue()
            md5 = hashlib.md5()
            md5.update(im)
            hash = md5.digest()
            data = Types.Data()
            data.size = res['size']
            data.bodyHash = hash
            data.body = im
            resource = Types.Resource()
            resource.mime = res['type']
            resource.data = data
            ourNote.resources.append(resource)
            hash_hex = binascii.hexlify(hash)
            insert = "<br /><en-media type=\"%s\" hash=\"%s\" /><br />" % (resource.mime, hash_hex)
            body = body.replace('<p id="'+res['name']+'"></p>', insert)

    body += "</en-note>"

    ourNote.content = body
    token = client.token
    ourNote.notebookGuid = guid

    try:
        client = get_evernote_client(token=token)
        note_store = client.get_note_store()
        note = note_store.createNote(token, ourNote)
    except Errors.EDAMUserException, edue:
        print "EDAMUserException:", edue
        return None
    except Errors.EDAMNotFoundException, ednfe:
        print "EDAMNotFoundException: Invalid parent notebook GUID"
        return None
    return {
        'guid': note.guid,
        'title': note.title,
        'content': body,
        'created': note.created,
        'updated': note.updated,
        'link_to_en_notebook': link_to_en
    }

def json_response_with_headers(data, status=200):
    response_data = data
    return HttpResponse(json.dumps(response_data), content_type="application/json")

def logout(request):
    if 'callback' in request.GET:
        url = request.GET.get('callback').decode("utf-8")
        response = redirect(url)
        response.delete_cookie('id')
        response.delete_cookie('access_token')
        response.delete_cookie('oauth_token')
        response.delete_cookie('oauth_token_secret')
        return response

def is_localhost():
    return 'HTTP_HOST' not in os.environ or os.environ['HTTP_HOST'].startswith("localhost")

def make_unicode(value):
    value = unicode(value, "utf-8")
