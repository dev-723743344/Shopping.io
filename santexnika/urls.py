from django.contrib import admin
from django.urls import path, include
from accounts.views import login_view, logout_view, home_redirect

urlpatterns = [
     path('admin/', admin.site.urls),

    # Root URL ("/") — foydalanuvchi login bo‘lganmi yoki yo‘qmi, tekshiradi
    path('', home_redirect, name='home'),

    path('clients/', include('clients.urls')),
    path('products/', include('products.urls')),
    path('sell/', include('sell.urls')),

    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),

    # Dashboard ichidagi sahifalar accounts.urls ichida bo‘lishi mumkin
    path('', include('accounts.urls')),
]
