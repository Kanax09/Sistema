from django.contrib import admin
from .models import *

class Clientesadmin(admin.ModelAdmin):
    fields=["CI","NAME","SURNAME","DIRECTION","BIRTHDATE","USERNAME","PASSWORD"]
    list_display= ["CI","NAME"]

admin.site.register(Clientes,Clientesadmin)

class Productosadmin(admin.ModelAdmin):
    fields=["PRODUCT_NAME","SIZE","TYPE","PRICE","STOCK"]
    list_display= ["ID_PRODUCT","PRODUCT_NAME"]

admin.site.register(Productos,Productosadmin)

class Pedidosadmin(admin.ModelAdmin):
    fields=["CLIENT","DATE","TIME"]
    list_display= ["ID_REQUEST","DATE","TIME"]

admin.site.register(Pedidos,Pedidosadmin)

class Detallesadmin(admin.ModelAdmin):
    fields=["ID_PEDIDO","PRODUCT","AMOUNT","TOTAL"]
    list_display= ["ID_DETAILS","ID_PEDIDO","PRODUCT","AMOUNT","TOTAL"]

admin.site.register(Detalles,Detallesadmin)

class user_adminadmin(admin.ModelAdmin):
    fields=["ADMIN_CI","PASSWORD"]
    list_display= ["ADMIN_CI","PASSWORD"]
admin.site.register(user_admin,user_adminadmin)