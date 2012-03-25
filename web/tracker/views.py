from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response
from tracker.models import *
from django.template import Context, loader, RequestContext
from datetime import datetime
from operator import itemgetter
from itertools import chain
from django.db.models import Q
from django.utils import simplejson

# Create your views here.

def home(request):
    return render_to_response('home.html')

def tracker(request):

    variables = {
        'page':'ticker'
    }

    return render_to_response('tracker.html', variables)    


def ticker(request, max=50, type=None, username=None, noteid=None):

    # limit max to 200
    max = int(max)
    if max > 200:
        max = 200

    # filter by type and/or username if given
    if type is not None and username is not None:
        new_events = events.objects.filter(
            Q(type=type),
            Q(from_user=username) | Q(to_user=username)
            ).order_by('-timestamp')[:max]
    elif type is not None and username is None:
        new_events = events.objects.filter(
            Q(type=type)
            ).order_by('-timestamp')[:max]
    elif type is None and username is not None:
        new_events = events.objects.filter(
            Q(from_user=username) | Q(to_user=username)
            ).order_by('-timestamp')[:max]
    elif noteid is not None:
        new_events = events.objects.filter(
            Q(note_id=noteid)
            ).order_by('-timestamp')[:max]
    else:
        new_events = events.objects.all().order_by('-timestamp')[:max]
        
    # get new notes
    new_notes = notes.objects.all()
    
    result_list = []
    
    for event in new_events:
        note = notes.objects.filter(id=event.note_id)[0]
        if event.note_id == note.id:
        
            result_list.append({
                'promise':note.promise,
                'timestamp':event.timestamp,
                'from_user':event.from_user,
                'to_user':event.to_user,
                'type':event.type,
                'note_id':event.note_id,
                'tweet_id':event.tweet_id,
            })
    
    final = sorted(result_list, key=itemgetter('timestamp'), reverse=True)
    
    variables = {
        'events':final,
    }

    return render_to_response('ticker.html', variables)    
    
def showlist(request):

    trust_list = trustlist.objects.all()
    
    variables = {
    
        'trustlist':trust_list,
        'page':'trustlist',
    
    }
    
    return render_to_response('force.html', variables)    


def user(request, username):

    variables = {}

    notes_bearer = notes.objects.filter(bearer=username).filter(status=0)
    notes_issuer = notes.objects.filter(issuer=username).filter(status=0)
    events_from = events.objects.filter(from_user=username)[:10]
    events_to = events.objects.filter(to_user=username)[:10]
 
    events_all = chain(events_from,events_to)
    
    result_list = []
    
    for event in events_all:
        note = notes.objects.filter(id=event.note_id)[0]
        if event.note_id == note.id:
        
            result_list.append({
                'promise':note.promise,
                'timestamp':event.timestamp,
                'from_user':event.from_user,
                'to_user':event.to_user,
                'type':event.type,
                'note_id':event.note_id,
                'tweet_id':event.tweet_id,
            })
    
    final = sorted(result_list, key=itemgetter('timestamp'), reverse=True)
    
    # Find number of people who trust this user
    trusters = trustlist.objects.filter(trusted=username)    
    trust_num = len(trusters)

    # Add trusters to list
    trusters_list = []
    for truster in trusters:
        trusters_list.append(truster.user)

    # Arbitrary, for now
    top_trusters = trusters_list[:1]

    # generate slug
    slug = username
    
    # combine events
    variables = {
        'username':username,
        'notes_held':notes_bearer,
        'notes_issued':notes_issuer,
        'events':final,
        'trust':trust_num,
        'trusters':trusters_list,
        'top_trusters':top_trusters
    }
    
    # return all
    return render_to_response('user.html', variables)
    

def getnote(request, noteid):

    note = notes.objects.get(id=noteid)
    new_events = events.objects.filter(note_id=noteid).order_by('timestamp')
    new_events = new_events.reverse()
    
    tweet = tweets.objects.get(tweet_id=noteid)
    
    id = str(note.id)
    
    variables = {
        'events':new_events,
        'note':note,
        'content':tweet.content,
        'id':id,
    }
    
    return render_to_response('note.html', variables)
    
    
def printer(request):
    variables = {
        'page':'printer',
    }
    return render_to_response('printer.html', variables)
    

def help(request):
    variables = {
        'page':'help',
    }
    return render_to_response('help.html', variables)

# [!] Check if for non-note ids too
def search(request, term=None):

    try:
        url = int(term)
        matching_events = events.objects.all().filter(tweet_id=term)[0]
        noteid = int(matching_events.note_id)
        url = '/note/' + str(noteid)
    except:
        url = '/user/' + term
    
    return HttpResponse(url)


'''
API Methods
'''

# Return trustnet as JSON
def trustnet(request):

    all_nodes = trustlist.objects.all()
    
    nodes = []
    checked = []
    for n in all_nodes:
        if n.user not in checked:
            nodes.append({"name":n.user, "group":1})
            checked.append(n.user)
        if n.trusted not in checked:
            nodes.append({"name":n.trusted, "group":1})
            checked.append(n.trusted)


    links = []
    for n in all_nodes:
        
        source = checked.index(n.user)
        target = checked.index(n.trusted)
    
        links.append({"source" : source, "target" : target, "value" : 1})
        
    graph = {"nodes" : nodes, "links" : links}
    
    data = simplejson.dumps(graph)
    
    return HttpResponse(data, mimetype='application/javascript')


# Returns user_info for trustnet sidebar   
def user_info(request, username):

    # Find number of people who trust this user
    trusted_by = trustlist.objects.filter(trusted=username)    
    trusted_num = len(trusted_by)

    # Add trusters to list
    trusted_list = []
    for t in trusted_by:
        trusted_list.append(t.user)

    # Find number of people who this user trusts
    trusts = trustlist.objects.filter(user=username)    
    trusts_num = len(trusts)
    
    # Add people user trusts to list
    trusts_list = []
    for t in trusts:
        trusts_list.append(t.trusted)
    
    # Return variables
    variables = {
        'trusted_num':trusted_num,
        'trusted':trusted_list,
        'trusts':trusts_list,
        'trusts_num':trusts_num,
        'username':username,
    }
    
    return render_to_response('user_info.html', variables)
    
    
    

    

