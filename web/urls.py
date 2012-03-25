from django.conf.urls.defaults import patterns, include, url

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    url(r'^$', 'tracker.views.home', name='home'),
    
    url(r'^tracker/$', 'tracker.views.tracker', name='tracker'),
    
    # ticker url patterns
    # max (optional) < user (optional) < type (optional) < note (optional)
    
    url(r'^ticker/$', 'tracker.views.ticker', name='ticker'),
    url(r'^ticker/max/(?P<max>\d+)/user/(?P<username>\w+)/type/(?P<type>\d{1})/$', 'tracker.views.ticker', name='ticker'),
    url(r'^ticker/max/(?P<max>\d+)/type/(?P<type>\d{1})/$', 'tracker.views.ticker', name='ticker'),
    url(r'^ticker/user/(?P<username>\w+)/type/(?P<type>\d{1})/$', 'tracker.views.ticker', name='ticker'),
    url(r'^ticker/max/(?P<max>\d+)/user/(?P<username>\w+)/$', 'tracker.views.ticker', name='ticker'),
    url(r'^ticker/max/(?P<max>\d+)/$', 'tracker.views.ticker', name='ticker'),
    url(r'^ticker/user/(?P<username>\w+)/$', 'tracker.views.ticker', name='ticker'),
    url(r'^ticker/type/(?P<type>\d{1})$', 'tracker.views.ticker', name='ticker'),
    url(r'^ticker/note/(?P<noteid>\d+)$', 'tracker.views.ticker', name='ticker'),
    
    # search
    
   url(r'^search/(?P<term>\w+)$', 'tracker.views.search', name='search'),
    
    # other patterns
    
    url(r'^trustlist/$', 'tracker.views.showlist', name='showlist'),
    
    url(r'^print/$', 'tracker.views.printer', name='showlist'),
    
    url(r'^user/(?P<username>\w+)$', 'tracker.views.user', name='user'),
    
    url(r'^note/(?P<noteid>\w+)$', 'tracker.views.getnote', name='note'),
    
    url(r'^help/$', 'tracker.views.help', name='help'),
    
    # trust list

    url(r'^graph/$', 'tracker.views.trustnet', name='graph'),
    
    url(r'^user_info/(?P<username>\w+)$', 'tracker.views.user_info', name='user_info'),
    
)
