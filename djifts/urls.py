from django.conf.urls import patterns, include, url


# Uncomment the next two lines to enable the admin:
import games.views
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'djifts.views.home', name='home'),
    # url(r'^djifts/', include('djifts.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),
    url(r'^teams/', include('teams.urls')),
    url(r'^games/', include('games.urls')),
)
