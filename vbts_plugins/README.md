0. Install in endaga server or separate plugin server
1. Add 'vbts_plugins' to INSTALLED_APPS in settings.py 
    Ex: INSTALLED_APPS = (
            .
            .
            .
            'vbts_plugins',
            .
        )
2. Make sure settings.py contains PCARI['CLOUD_URL']
    PCARI = {
        'CLOUD_URL': 'http://127.0.0.1:8000/server/'
    }
3. Include vbts_plugins.urls to your project's urls.py
    Ex: url(r'^server/', include('vbts_plugins.urls'),
            name='server-plugins'),
            