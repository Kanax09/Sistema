"""
URL configuration for Sistema project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
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
from django.contrib import admin
from django.urls import path
from APP import views

urlpatterns = [
    path('', views.login_usuario, name='index'),
    path('login-usuario/', views.login_usuario, name='login_usuario'),
    path('register-user/', views.register_user, name='register_user'),
    path('catalogo/', views.catalogo_user, name='catalogo_user'),
    path('agregar-al-carrito/', views.agregar_al_carrito, name='agregar_al_carrito'),
    path('carrito/', views.ver_carrito, name='ver_carrito'),
    path('actualizar-carrito/', views.actualizar_carrito, name='actualizar_carrito'),
    path('eliminar-del-carrito/', views.eliminar_del_carrito, name='eliminar_del_carrito'),
    path('actualizar-carrito-lote/', views.actualizar_carrito_lote, name='actualizar_carrito_lote'),
    path('vaciar-carrito/', views.vaciar_carrito, name='vaciar_carrito'),
    path('checkout/', views.checkout, name='checkout'),

    path('login-admin/', views.login_admin, name='login_admin'),
    path('admin-catalogo/', views.admin_catalogo, name='admin_catalogo'),
    path('admin-catalogo/crear/', views.crear_producto, name='crear_producto'),
    path('admin-catalogo/editar/<int:producto_id>/', views.editar_producto, name='editar_producto'),
    path('eliminar-producto/<int:producto_id>/', views.eliminar_producto, name='eliminar_producto'),
    path('backup/', views.backup_database, name='backup_database'),
    path('restore/', views.restore_database, name='restore_database'),
    path('panel-ventas/', views.panel_ventas, name='panel_ventas'),
    path('panel-ventas/<int:pedido_id>/', views.detalle_pedido, name='detalle_pedido'),
    

    path('admin/', admin.site.urls),
]
