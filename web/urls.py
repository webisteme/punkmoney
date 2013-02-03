from django.conf.urls.defaults import patterns, include, url

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

from django.contrib.auth.views import login, logout

urlpatterns = patterns('',

    # Examples:
    url(r'^$', 'tracker.views.home', name='home'),
    
    url(r'^tracker/$', 'tracker.views.tracker', name='tracker'),
    
    url(r'^t/(?P<tag_1>\w+)/$', 'tracker.views.tracker', name='tracker'),
    url(r'^t/(?P<tag_1>\w+)/(?P<tag_2>\w+)/$', 'tracker.views.tracker', name='tracker'),
    url(r'^t/(?P<tag_1>\w+)/(?P<tag_2>\w+)/(?P<tag_3>\w+)/$', 'tracker.views.tracker', name='tracker'),
    
    # ticker url patterns
    # max (optional) < user (optional) < type (optional) < note (optional)
    
    url(r'^ticker/$', 'tracker.views.ticker', name='ticker'),
    url(r'^ticker/max/(?P<max>\d+)/user/(?P<username>\w+)/type/(?P<type>\d+)/$', 'tracker.views.ticker', name='ticker'),
    url(r'^ticker/max/(?P<max>\d+)/type/(?P<type>\d+)/$', 'tracker.views.ticker', name='ticker'),
    url(r'^ticker/user/(?P<username>\w+)/type/(?P<type>\d_)/$', 'tracker.views.ticker', name='ticker'),
    url(r'^ticker/max/(?P<max>\d+)/user/(?P<username>\w+)/$', 'tracker.views.ticker', name='ticker'),
    url(r'^ticker/max/(?P<max>\d+)/$', 'tracker.views.ticker', name='ticker'),
    url(r'^ticker/user/(?P<username>\w+)/$', 'tracker.views.ticker', name='ticker'),
    url(r'^ticker/type/(?P<type>\d+)$', 'tracker.views.ticker', name='ticker'),
    url(r'^ticker/note/(?P<noteid>\d+)$', 'tracker.views.ticker', name='ticker'),
    
    # Tags only
    
    url(r'^ticker/tags/(?P<tag_1>\w+)/$', 'tracker.views.ticker', name='ticker'),
    url(r'^ticker/tags/(?P<tag_1>\w+)/(?P<tag_2>\w+)/$', 'tracker.views.ticker', name='ticker'),
    url(r'^ticker/tags/(?P<tag_1>\w+)/(?P<tag_2>\w+)/(?P<tag_3>\w+)/$', 'tracker.views.ticker', name='ticker'),
    
    # Type with tags
    
    url(r'^ticker/type/(?P<type>\d+)/tags/(?P<tag_1>\w+)/$', 'tracker.views.ticker', name='ticker'),
    url(r'^ticker/type/(?P<type>\d+)/tags/(?P<tag_1>\w+)/(?P<tag_2>\w+)/$', 'tracker.views.ticker', name='ticker'),
    url(r'^ticker/type/(?P<type>\d+)/tags/(?P<tag_1>\w+)/(?P<tag_2>\w+)/(?P<tag_3>\w+)/$', 'tracker.views.ticker', name='ticker'),
    
    # search
    
    url(r'^search/(?P<term>.*)$', 'tracker.views.search', name='search'),
    
    # wallet
    
    url(r'^wallet/$', 'tracker.views.wallet', name='wallet'),
    
    # other patterns
    
    url(r'^trustnet/$', 'tracker.views.shownet', name='trustnet'),
    url(r'^print/$', 'tracker.views.printer', name='showlist'),
    url(r'^user/(?P<username>\w+)$', 'tracker.views.user', name='user'),
    url(r'^note/(?P<noteid>\w+)$', 'tracker.views.getnote', name='note'),
    url(r'^help/$', 'tracker.views.help', name='help'),
    
    # registration
    
    url(r'^social/', include('web.socialregistration.urls', namespace = 'socialregistration')),
    
    # trust list

    url(r'^graph/$', 'tracker.views.trustnet', name='graph'),
    url(r'^user_info/(?P<username>\w+)$', 'tracker.views.user_info', name='user_info'),
    
    # admin
    
    url(r'^admin/', include(admin.site.urls)),
    
    # auth URLs...
    
    url(r'^login/$',  login),
    url(r'^logout/$', logout, {'next_page': '/'})

)
