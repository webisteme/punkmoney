import uuid
import urllib2
import simplejson

def generate_username(user, profile, client):
    """
    Default function to generate usernames using the built in `uuid` library.
    """
    
    #PM - get user screenname from Twitter
    url = "https://api.twitter.com/1/users/show.json?id=%s" % profile.twitter_id
    
    raw_data = urllib2.urlopen(url)

    data = {}
    for d in raw_data:
        data = simplejson.loads(d)
    
    return data['screen_name']
