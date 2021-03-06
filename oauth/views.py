# -*- coding: utf-8 -*-
from evernote.api.client import EvernoteClient
from evernote.api.client import Store
from evernote.edam.type.ttypes import (
    Note
)
from evernote.edam.type.ttypes import NoteSortOrder
import evernote.edam.type.ttypes as Types
import evernote.edam.error.ttypes as Errors
import evernote.edam.notestore.NoteStore as NoteStore

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
import StringIO
import pycurl
import re
import base64
from datetime import date

sandbox = True

if sandbox:
    base_url = 'https://sandbox.evernote.com'
else:
    base_url = 'https://www.evernote.com'

link_to_en = base_url + '/Home.action'

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
    access_token = ''
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
    if len(access_token) > 0 :
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
    response = redirect(client.get_authorize_url(request_token) + '&supportLinkedSandbox=true&suggestedNotebookName=Markdown')
    response.set_cookie('oauth_token', request_token['oauth_token'])
    response.set_cookie('oauth_token_secret', request_token['oauth_token_secret'])
    return response

def get_info(request):
    try:
        token = request.COOKIES['access_token']
        client = get_evernote_client(token=token)
    except KeyError:
        return json_response_with_headers({
            'status': 'redirect',
            'redirect_url': '/login/',
            'home_url': link_to_en,
            'msg': 'Login to use'
        })
    user_store = client.get_user_store()
    user_info = user_store.getUser()

    note_store = client.get_note_store()
    notebooks = note_store.listNotebooks()

    if len(notebooks) < 1 :
        return json_response_with_headers({
            'status': 'warning',
            'redirect_url': '/logout/',
            'msg': 'No Notebook',
            'notebook': {},
            'home_url': link_to_en,
            'username': user_info.username
        })
    guid = notebooks[0].guid
    notebook = note_store.getNotebook(guid)
    response = json_response_with_headers({
            'status': 'success',
            'redirect_url': '/logout/',
            'msg': 'Logout',
            'home_url': link_to_en,
            'notebook': {'guid':notebook.guid, 'name':notebook.name},
            'username': user_info.username
    })
    response.set_cookie('guid', guid)
    return response


def reset(request):
    return redirect('/')

def import_note_content(request):
    try :
        token = request.COOKIES['access_token']
        note_id = request.POST['note_id']
    except Exception as e:
        return redirect('/login/')
    url = base_url + '/note/' + note_id
    c = pycurl.Curl()
    c.setopt(c.URL, url)
    c.setopt(c.COOKIE, 'auth='+token)
    c.setopt(c.VERBOSE, 1)
    buf = StringIO.StringIO()
    c.setopt(c.WRITEFUNCTION, buf.write)
    c.perform()
    content = buf.getvalue()
    c.close()




    # resources = []
    # r = re.compile('<img[^>]+>')
    # imageTags = r.findall(content)
    # for i in imageTags:
    #     r2 = re.compile('src="(.+?res\/(.+?)\.png[^"]+)"')
    #     resource = r2.search(i)
    #     name = resource.group(2)
    #     src = resource.group(1) + '&auth=' + token
    #     id = name+'_'+str(date.today().year)
    #     resources.append({
    #         'id': id,
    #         'name': name,
    #         'src': encodeImg(src)['src'],
    #         'type': encodeImg(src)['type'],
    #         'size': encodeImg(src)['size']
    #     })
    #     insert = '\n !['+name+']('+id+' "'+name+'") \n'
    #     content = content.replace(i, insert)

    return json_response_with_headers({
        'status': 'success',
        'msg': 'content',
        'note_id': note_id,
        'content': content,
        # 'resources': resources
    })

def import_note(request):
    try :
        token = request.COOKIES['access_token']
        guid = request.COOKIES['guid']
    except Exception as e:
        return redirect('/login/')
    client = get_evernote_client(token=token)
    note_store = client.get_note_store()
    note_filter = NoteStore.NoteFilter()
    note_filter.notebookGuid = guid
    note_filter.order = NoteSortOrder.UPDATED

    search_spec = NoteStore.NotesMetadataResultSpec()
    search_spec.includeAttributes = True;
    search_spec.includeCreated = True;
    search_spec.includeUpdated = True;
    search_spec.includeTitle = True;

    notes = []
    try :
        noteList = note_store.findNotesMetadata(token, note_filter, 0, 10, search_spec)
        for n in noteList.notes:
            notes.append({
                "title": n.title,
                "note_id": n.guid,
                "updated": n.updated
            })

    except Errors.EDAMUserException, edue:
        print "EDAMUserException:", edue
        return json_response_with_headers({
            'status': 'error',
            'msg': 'user permission error',
        })
    except Errors.EDAMNotFoundException, ednfe:
        print "EDAMNotFoundException: Invalid parent notebook GUID"
        return json_response_with_headers({
            'status': 'error',
            'msg': 'no find note',
        })
    return json_response_with_headers({
        'status': 'success',
        'msg': 'notes',
        'notes': notes,
    })

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
            file = StringIO.StringIO(urllib.urlopen(src).read())
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

def encodeImg(src):
    try:
        image = urllib.urlopen(src)
        http_message = image.info()
        image_type = ''
        if 'png' in http_message.type:
            image_type = 'png'
        elif 'jpeg' in http_message.type:
            image_type = 'jpg'
        elif 'gif' in http_message.type:
            image_type = 'gif'
        image_64 = base64.encodestring(image.read())
        src = 'data:image/' + image_type + ';base64,' + image_64
        return {
            'src': src,
            'type': http_message.type,
            'size': len(src)
        }
    except Exception as e:
        print e
        return src
