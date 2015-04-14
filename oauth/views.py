from evernote.api.client import EvernoteClient

from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response
from django.shortcuts import redirect
from django.http import HttpResponse
import json
import Cookie
import os
import socket
import oauth2 as oauth
import urllib
import urlparse

EN_CONSUMER_KEY = 'junterai-0563'
EN_CONSUMER_SECRET = '2af8adbdb0bd2f7b'


def get_evernote_client(token=None):
    if token:
        return EvernoteClient(token=token, sandbox=True)
    else:
        return EvernoteClient(
            consumer_key=EN_CONSUMER_KEY,
            consumer_secret=EN_CONSUMER_SECRET,
            sandbox=True
        )


def index(request):
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


            # access_token =client.get_access_token(
            #     request.session['_evernote_oauth_token'],
            #     request.session['_evernote_oauth_token_secret'],
            #     request.GET.get("oauth_verifier", '')
            # )

            # user_store = client.get_user_store()
            # user = user_store.getUser()
            # username = user.username
            # shard_id = user.shardId
            # privilege = user.privilege
            
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

def get_access_token(self, oauth_token, oauth_token_secret, oauth_verifier):
    token = oauth.Token(oauth_token, oauth_token_secret)
    token.set_verifier(oauth_verifier)
    client = _get_oauth_client(token)

    resp, content = client.request(self._get_endpoint('oauth'), 'POST')
    access_token = dict(urlparse.parse_qsl(content))
    self.token = access_token['oauth_token']
    return self.token

def _get_oauth_client(self, token=None):
    consumer = oauth.Consumer(self.consumer_key, self.consumer_secret)
    if token:
        client = oauth.Client(consumer, token)
    else:
        client = oauth.Client(consumer)
    return client


def callback(request):
    try:
        client = get_evernote_client()
        client.get_access_token(
            request.session['oauth_token'],
            request.session['oauth_token_secret'],
            request.session['oauth_verifier']
        )
    except KeyError:
        return json_response_with_headers({
            'status': 'redirect',
            'redirect_url': '/login/',
            'msg': 'Need to Login'
        })

    note_store = client.get_note_store()
    notebooks = note_store.listNotebooks()

    notes = [];
    if notebooks is not None:
        for note in notebooks:
            name = note.name
            notes.append({
                'name': name
            })

    return json_response_with_headers({
            'status': 'success',
            'redirect_url': '/logout/',
            'msg': 'Logout',
            'notebooks': notes
    })

def reset(request):
    return redirect('/')

def make_note(authToken, noteStore, noteTitle, noteBody, resources=[], parentNotebook=None):
    """
    Create a Note instance with title and body 
    Send Note object to user's account
    """

    ourNote = Types.Note()
    ourNote.title = noteTitle

    ## Build body of note

    nBody = "<?xml version=\"1.0\" encoding=\"UTF-8\"?>"
    nBody += "<!DOCTYPE en-note SYSTEM \"http://xml.evernote.com/pub/enml2.dtd\">"
    nBody += "<en-note>%s" % noteBody
    if resources:
        ### Add Resource objects to note body
        nBody += "<br />" * 2
        ourNote.resources = resources
        for resource in resources:
            hexhash = binascii.hexlify(resource.data.bodyHash)
            nBody += "Attachment with hash %s: <br /><en-media type=\"%s\" hash=\"%s\" /><br />" % \
                (hexhash, resource.mime, hexhash)
    nBody += "</en-note>"

    ourNote.content = nBody

    ## parentNotebook is optional; if omitted, default notebook is used
    if parentNotebook and hasattr(parentNotebook, 'guid'):
        ourNote.notebookGuid = parentNotebook.guid

    ## Attempt to create note in Evernote account
    try:
        note = noteStore.createNote(authToken, ourNote)
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
    return note

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