from evernote.api.client import EvernoteClient
from evernote.api.client import Store
from evernote.edam.type.ttypes import (
    Note,
)
import evernote.edam.error.ttypes as Errors
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response
from django.shortcuts import redirect
from django.http import HttpResponse
from django.middleware.csrf import get_token
import json
import Cookie
import os
import socket
import oauth2 as oauth
import urllib
import urlparse

EN_CONSUMER_KEY = 'junterai-0563'
EN_CONSUMER_SECRET = '2af8adbdb0bd2f7b'
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
            consumer_key=EN_CONSUMER_KEY,
            consumer_secret=EN_CONSUMER_SECRET,
            sandbox=sandbox
        )


def index(request):
    csrf_token = get_token(request)
    return render_to_response('oauth/index.html')


def auth(request):
    client = get_evernote_client()
    try:
        user_store = client.get_user_store()
        user_store.getUser()
        if '_redirect_url' in request.session:
            redirect_uri = request.session['_redirect_url']
            del request.session['_redirect_url']
            return redirect(redirect_uri)
        return redirect(url_for('/'))
    except Exception as e:
        # callbackUrl = 'http://%s/login/' % (get_hostname())
        callbackUrl = 'http://localhost:8000/login/'
        client = get_evernote_client()
        request_token = client.get_request_token(callbackUrl)

    # Save the request token information for later
    request.session['oauth_token'] = request_token['oauth_token']
    request.session['oauth_token_secret'] = request_token['oauth_token_secret']

    # Redirect the user to the Evernote authorization URL
    return redirect(client.get_authorize_url(request_token))


def login(request):
    if 'callback' in request.GET:
        request.session['_redirect_url'] = request.GET.get('callback').decode("utf-8")
    elif not request.session['_redirect_url'] :
        request.session['_redirect_url'] = 'http://www.nikkei.com'

    try:
        client = get_evernote_client()
        if 'oauth_verifier' in request.GET:
            request.session['oauth_verifier'] = request.GET.get("oauth_verifier")

            # access_token = client.get_access_token(
            #      request.session['oauth_token'],
            #      request.session['oauth_token_secret'],
            #      request.session['oauth_verifier']
            #  )
            # client = EvernoteClient(token=access_token)
            # user_store = client.get_user_store()
            # user = user_store.getUser()
            # username = user.username
            # shard_id = user.shardId
            # privilege = user.privilege
            
            # request.session['shard_id'] = shard_id

            # entity = Evernote(
            #     key_name=key_name,
            #     user_id=user.id,
            #     shard_id=shard_id,
            #     username=username,
            #     privilege=privilege,
            #     access_token=access_token)
            # entity.put()
            # # model = auth_model_class(
            #     key_name=key_name,
            #     evernote=entity,
            # )
            # auth_model_class.insert_or_update(model)

        else :
            return redirect('/auth/')
    except Exception as e:
        return redirect('http://www.google.com/')
    if '_redirect_url' in request.session:
        redirect_uri = request.session['_redirect_url']
        del request.session['_redirect_url']
        return redirect(redirect_uri)


def get_info(request):
    try:
        client = get_evernote_client()
        request.session['access_token'] = client.get_access_token(
            request.session['oauth_token'],
            request.session['oauth_token_secret'],
            request.session['oauth_verifier']
        )
    except KeyError:
        return json_response_with_headers({
            'status': 'redirect',
            'redirect_url': '/login/',
            'home_url': link_to_en,
            'msg': 'Login'
        })

    note_store = client.get_note_store()
    notebooks = note_store.listNotebooks()

    notes = [];
    if notebooks is not None:
        for note in notebooks:
            name = note.name
            guid = note.guid
            notes.append({
                'name': name,
                'guid': guid
            })
    return json_response_with_headers({
            'status': 'success',
            'redirect_url': '/logout/',
            'msg': 'Logout',
            'home_url': link_to_en,
            'notebooks': notes
    })

def reset(request):
    return redirect('/')

def note(request):
    request.token = request.session['access_token']
    if 'title' in request.POST:
        title = request.POST.get('title', '').encode('utf-8')
    if 'body' in request.POST:
        body = request.POST.get('body', '').encode('utf-8')
    if 'resources' in request.POST:
        resources = request.POST.get('resources', '')
    if 'guid' in request.POST:
        guid = request.POST.get('guid', '')
    try:
        note = make_note(request, title, body, resources, guid)
        return json_response_with_headers({
            'status': 'success',
            'note': note
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
    body += "<en-note>%s</en-note>" % noteBody.encode('utf-8')

    ourNote = Note()
    ourNote.title = noteTitle
    ourNote.content = body
    token = client.token

    # if resources:
    #     ### Add Resource objects to note body
    #     body += "<br />" * 2
    #     note.resources = resources
    #     for resource in resources:
    #         hexhash = binascii.hexlify(resource.data.bodyHash)
    #         body += "Attachment with hash %s: <br /><en-media type=\"%s\" hash=\"%s\" /><br />" % \
    #             (hexhash, resource.mime, hexhash)


    ## parentNotebook is optional; if omitted, default notebook is used
    # if parentNotebook and hasattr(parentNotebook, 'guid'):
    ourNote.notebookGuid = guid

    ## Attempt to create note in Evernote account

    try:
        client = get_evernote_client(token=token)
        note_store = client.get_note_store()
        note = note_store.createNote(token, ourNote)
    except Errors.EDAMUserException, edue:
        ## Something was wrong with the note data
        ## See EDAMErrorCode enumeration for error code explanation
        ## http://dev.evernote.com/documentation/reference/Errors.html#Enum_EDAMErrorCode
        print "EDAMUserException:", edue
        return None
    except Errors.EDAMNotFoundException, ednfe:
        ## Parent Notebook GUID doesn't correspond to an actual notebook
        print "EDAMNotFoundException: Invalid parent notebook GUID"
        return None
    ## Return created note object
    return {
        'guid': note.guid,
        'title': note.title,
        # 'thumbnail': thumbnail,
        'content': body,
        'created': note.created,
        'updated': note.updated,
    }

def json_response_with_headers(data, status=200):
    response_data = data
    return HttpResponse(json.dumps(response_data), content_type="application/json")

def logout(request):
    request.session.clear()
    if 'callback' in request.GET:
        url = request.GET.get('callback').decode("utf-8")
        return redirect(url)

def get_hostname():
    try:
        HOSTNAME = socket.gethostname()
    except:
        HOSTNAME = 'localhost:8000'
    return HOSTNAME

def is_localhost():
    return 'HTTP_HOST' not in os.environ or os.environ['HTTP_HOST'].startswith("localhost")
