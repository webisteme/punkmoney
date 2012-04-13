from django.db import models

class events(models.Model):
    id = models.IntegerField(primary_key=True)
    note_id = models.BigIntegerField(null=True, blank=True)
    tweet_id = models.BigIntegerField()
    type = models.IntegerField(null=True, blank=True)
    timestamp = models.DateTimeField()
    from_user = models.CharField(max_length=90)
    to_user = models.CharField(max_length=90)
    class Meta:
        db_table = u'tracker_events'

class notes(models.Model):
    id = models.BigIntegerField(max_length=30, primary_key=True)
    issuer = models.CharField(max_length=90, blank=True)
    bearer = models.CharField(max_length=90, blank=True)
    promise = models.CharField(max_length=420, blank=True)
    created = models.DateTimeField(null=True, blank=True)
    expiry = models.DateTimeField(null=True, blank=True)
    status = models.IntegerField(null=True, blank=True)
    transferable = models.IntegerField(null=True, blank=True)
    type = models.IntegerField(null=True, blank=True)
    class Meta:
        db_table = u'tracker_notes'

class trustlist(models.Model):
    id = models.IntegerField(primary_key=True)
    user = models.CharField(max_length=90, blank=True)
    trusted = models.CharField(max_length=90, blank=True)
    class Meta:
        db_table = u'tracker_trust_list'

class tweets(models.Model):
    id = models.IntegerField(primary_key=True)
    timestamp = models.DateTimeField(null=True, blank=True)
    tweet_id = models.BigIntegerField(null=True, blank=True)
    author = models.CharField(max_length=90, blank=True)
    content = models.CharField(max_length=420, blank=True)
    reply_to_id = models.BigIntegerField(null=True, blank=True)
    parsed = models.CharField(max_length=1, null=True, blank=True) #! fix
    class Meta:
        db_table = u'tracker_tweets'

class users(models.Model):
    id = models.IntegerField(primary_key=True)
    username = models.CharField(max_length=90, blank=True)
    karma = models.IntegerField(null=True, blank=True)
    class Meta:
        db_table = u'tracker_users'