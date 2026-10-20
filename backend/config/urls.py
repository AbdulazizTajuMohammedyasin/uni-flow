"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

import inngest.django
from django.contrib import admin
from django.urls import include, path

from config.inngest import client, functions

urlpatterns = [
    # Back-office for developers and super admins only; the staff UI is the React /staff area.
    path("django-admin/", admin.site.urls),
    # The versioned REST API used by the web app (and later the mobile app).
    path("api/v1/", include("config.api_v1")),
    # Inngest calls this to run background jobs (config/inngest.py); online every call must be
    # signed with INNGEST_SIGNING_KEY, and unsigned calls are refused.
    inngest.django.serve(client, functions),
]
