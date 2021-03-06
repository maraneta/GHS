from django.conf.urls.defaults import patterns, include, url

from hazard_calculator.models import GHSIngredient

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('hazard_calculator.views',
    # Examples:
    # url(r'^$', 'ghs.views.home', name='home'),
    # url(r'^ghs/', include('ghs.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # url(r'^admin/', include(admin.site.urls)),
    
    (r'^hazard_calculator/$', 'hazard_calculator'),
    (r'^ingredient_autocomplete/$', 'ingredient_autocomplete'),
)
