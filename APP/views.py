# APP/views.py
import json
import os
import subprocess
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse, Http404
from django.db import transaction
from django.utils import timezone
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.middleware.csrf import get_token
from django.contrib.auth.hashers import make_password, check_password
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from .models import Productos, Clientes, Pedidos, Detalles
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login
import os
import sqlite3
from django.conf import settings
from django.contrib import messages
from django.shortcuts import render, redirect
from django.db import connection
from .forms import RestoreDBForm

from .models import  user_admin
from .forms import ClienteRegistrationForm
 # Para mostrar errores elegantes


def login_admin(request):
    if request.method == 'POST':
        cedula = request.POST.get('cedula', '').strip()
        password = request.POST.get('password')

        try:
            # Buscamos el administrador en la tabla personalizada
            admin_db = user_admin.objects.get(ADMIN_CI=cedula)
            
            # NOTA: Se recomienda usar check_password() y almacenar hashes.
            # Por ahora mantenemos la lógica de texto plano de tu modelo.
            if admin_db.PASSWORD == password:
                # Obtenemos o creamos el usuario de Django para que @login_required funcione
                user, created = User.objects.get_or_create(username=cedula)
                if created:
                    user.is_staff = True
                    user.save()

                request.session.flush()
                login(request, user)
                
                # Persistencia de datos adicionales en sesión
                request.session['cliente_id'] = admin_db.ADMIN_CI
                request.session['es_admin'] = True
                
                messages.success(request, 'Sesión de administrador iniciada.')
                return redirect('admin_catalogo')
            else:
                messages.error(request, 'Contraseña de administrador incorrecta.')
        
        except user_admin.DoesNotExist:
            messages.error(request, 'El administrador con esa cédula no existe.')

    return render(request, 'login-admin.html')

def login_usuario(request):
    if request.method == 'POST':
        cedula = request.POST.get('cedula', '').strip()
        password = request.POST.get('password')

        try:
            # Buscamos en la tabla Clientes
            cliente = Clientes.objects.get(CI=cedula)
            
            if check_password(password, cliente.PASSWORD):
                # Sincronizamos con el sistema de usuarios de Django
                user, created = User.objects.get_or_create(
                    username=cliente.USERNAME,
                    defaults={'first_name': cliente.NAME, 'last_name': cliente.SURNAME}
                )
                
                request.session.flush() 
                login(request, user)
                
                # Guardamos el CI para lógica de negocio existente
                request.session['cliente_id'] = cliente.CI
                
                messages.success(request, f'Bienvenido, {cliente.NAME}')
                return redirect('catalogo_user')
            else:
                messages.error(request, 'Cédula o contraseña incorrecta.')
        except Clientes.DoesNotExist:
            messages.error(request, 'El usuario con esa cédula no existe.')
            
    return render(request, 'login-usuario.html')

def register_user(request):
    if request.method == 'POST':
        form = ClienteRegistrationForm(request.POST)
        if form.is_valid():
            # Creamos el objeto pero no lo guardamos aún para hashear la clave
            nuevo_cliente = form.save(commit=False)
            nuevo_cliente.PASSWORD = make_password(form.cleaned_data['PASSWORD'])
            nuevo_cliente.save()
            messages.success(request, 'Usuario registrado con éxito. Ahora puedes iniciar sesión.')
            return redirect('login_usuario')
    else:
        form = ClienteRegistrationForm()
    
    return render(request, 'register-user.html', {'form': form})


# ---------- FUNCIONES AUXILIARES ----------
def get_cliente_from_user(user):
    """Obtiene el objeto Clientes asociado al User de Django (por username)."""
    if not user.is_authenticated:
        return None
    try:
        cliente = Clientes.objects.get(USERNAME=user.username)
    except Clientes.DoesNotExist:
        # Si no existe, lo creamos automáticamente con datos básicos
        cliente = Clientes.objects.create(
            CI=user.username,           # Temporal
            NAME=user.first_name or user.username,
            SURNAME=user.last_name or '',
            DIRECTION='Sin dirección',
            BIRTHDATE='2000-01-01',
            USERNAME=user.username,
            PASSWORD=''
        )
    return cliente

# ---------- VISTAS DE CATÁLOGO Y CARRITO ----------
@login_required
def catalogo_user(request):
    productos = Productos.objects.all()
    cliente = get_cliente_from_user(request.user)
    context = {
        'productos': productos,
        'cliente_nombre': cliente.NAME if cliente else request.user.username
    }
    return render(request, 'catalago-user.html', context)

@login_required
@transaction.atomic
def agregar_al_carrito(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    data = json.loads(request.body)
    producto_id = data.get('producto_id')
    cantidad = int(data.get('cantidad', 0))
    
    if cantidad <= 0:
        return JsonResponse({'error': 'Cantidad inválida'}, status=400)
    
    producto = Productos.objects.select_for_update().get(ID_PRODUCT=producto_id)
    
    if producto.STOCK < cantidad:
        return JsonResponse({'error': f'Stock insuficiente. Disponible: {producto.STOCK}'}, status=400)
    
    producto.STOCK -= cantidad
    producto.save()
    
    carrito = request.session.get('carrito', {})
    pid = str(producto_id)
    if pid in carrito:
        carrito[pid]['cantidad'] += cantidad
    else:
        carrito[pid] = {
            'nombre': producto.PRODUCT_NAME,
            'precio': str(producto.PRICE),
            'cantidad': cantidad
        }
    request.session['carrito'] = carrito
    request.session['ultima_actividad_carrito'] = timezone.now().isoformat()
    request.session.modified = True
    
    return JsonResponse({'success': True, 'mensaje': f'{cantidad} x {producto.PRODUCT_NAME} agregado(s)'})

@login_required
def ver_carrito(request):
    carrito = request.session.get('carrito', {})
    items = []
    total = 0
    total_unidades = 0
    for pid, item in carrito.items():
        subtotal = float(item['precio']) * item['cantidad']
        total += subtotal
        total_unidades += item['cantidad']
        items.append({
            'id': pid,
            'nombre': item['nombre'],
            'precio': item['precio'],
            'cantidad': item['cantidad'],
            'subtotal': subtotal
        })
    cliente = get_cliente_from_user(request.user)
    context = {
        'items': items,
        'total': total,
        'total_unidades': total_unidades,
        'cliente_nombre': cliente.NAME if cliente else request.user.username
    }
    return render(request, 'catalogo.html', context)

@login_required
@transaction.atomic
def actualizar_carrito(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    data = json.loads(request.body)
    pid = str(data.get('producto_id'))
    nueva = int(data.get('cantidad', 0))
    
    carrito = request.session.get('carrito', {})
    if pid not in carrito:
        return JsonResponse({'error': 'Producto no está en el carrito'}, status=400)
    
    producto = Productos.objects.select_for_update().get(ID_PRODUCT=int(pid))
    anterior = carrito[pid]['cantidad']
    diff = nueva - anterior
    
    if diff > 0 and producto.STOCK < diff:
        return JsonResponse({'error': f'Stock insuficiente. Solo hay {producto.STOCK} adicionales.'}, status=400)
    
    producto.STOCK -= diff
    producto.save()
    
    if nueva == 0:
        del carrito[pid]
    else:
        carrito[pid]['cantidad'] = nueva
    
    request.session['carrito'] = carrito
    request.session['ultima_actividad_carrito'] = timezone.now().isoformat()
    request.session.modified = True
    return JsonResponse({'success': True})

@login_required
@transaction.atomic
def actualizar_carrito_lote(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    data = json.loads(request.body)
    updates = data.get('items', [])
    carrito = request.session.get('carrito', {})
    
    for update in updates:
        pid = str(update['producto_id'])
        nueva = int(update['cantidad'])
        if pid not in carrito:
            continue
        try:
            producto = Productos.objects.select_for_update().get(ID_PRODUCT=int(pid))
        except Productos.DoesNotExist:
            # Producto eliminado: lo quitamos del carrito y continuamos
            del carrito[pid]
            continue
        
        anterior = carrito[pid]['cantidad']
        diff = nueva - anterior
        if diff > 0 and producto.STOCK < diff:
            return JsonResponse({'error': f'Stock insuficiente para {producto.PRODUCT_NAME}'}, status=400)
        producto.STOCK -= diff
        producto.save()
        if nueva == 0:
            del carrito[pid]
        else:
            carrito[pid]['cantidad'] = nueva
    
    request.session['carrito'] = carrito
    request.session['ultima_actividad_carrito'] = timezone.now().isoformat()
    request.session.modified = True
    return JsonResponse({'success': True})

@login_required
@transaction.atomic
def vaciar_carrito(request):
    carrito = request.session.get('carrito', {})
    for pid in list(carrito.keys()):
        try:
            producto = Productos.objects.select_for_update().get(ID_PRODUCT=int(pid))
            producto.STOCK += carrito[pid]['cantidad']
            producto.save()
        except Productos.DoesNotExist:
            # El producto ya no existe, simplemente lo ignoramos
            pass
        del carrito[pid]
    request.session['carrito'] = {}
    request.session.modified = True
    return JsonResponse({'success': True})

@login_required
@transaction.atomic
def eliminar_del_carrito(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    data = json.loads(request.body)
    pid = str(data.get('producto_id'))
    
    carrito = request.session.get('carrito', {})
    if pid in carrito:
        cantidad = carrito[pid]['cantidad']
        try:
            producto = Productos.objects.select_for_update().get(ID_PRODUCT=int(pid))
            producto.STOCK += cantidad
            producto.save()
        except Productos.DoesNotExist:
            # Producto ya no existe, no hay stock que devolver
            pass
        del carrito[pid]
        request.session['carrito'] = carrito
        request.session['ultima_actividad_carrito'] = timezone.now().isoformat()
        request.session.modified = True
    return JsonResponse({'success': True})

@login_required
@transaction.atomic
def checkout(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    carrito = request.session.get('carrito', {})
    if not carrito:
        return JsonResponse({'error': 'Carrito vacío'}, status=400)
    
    cliente = get_cliente_from_user(request.user)
    if not cliente:
        return JsonResponse({'error': 'Cliente no encontrado'}, status=400)
    
    pedido = Pedidos.objects.create(
        CLIENT=cliente,
        DATE=timezone.now().date(),
        TIME=timezone.now().time()
    )
    
    total_general = 0
    detalles_list = []
    
    for pid, item in list(carrito.items()):
        try:
            producto = Productos.objects.select_for_update().get(ID_PRODUCT=int(pid))
        except Productos.DoesNotExist:
            # Producto eliminado: limpiar del carrito y cancelar transacción
            del carrito[pid]
            request.session['carrito'] = carrito
            request.session.modified = True
            transaction.set_rollback(True)
            return JsonResponse({'error': f'El producto "{item["nombre"]}" ya no está disponible.'}, status=400)
        
        cantidad = item['cantidad']
        precio = float(item['precio'])
        
        # Verificación de seguridad (no debería ocurrir si el stock se manejó bien)
        if producto.STOCK < 0:
            transaction.set_rollback(True)
            return JsonResponse({'error': f'Stock inconsistente para {producto.PRODUCT_NAME}'}, status=400)
        
        subtotal = precio * cantidad
        total_general += subtotal
        
        detalles_list.append(Detalles(
            ID_PEDIDO=pedido,
            PRODUCT=producto,
            AMOUNT=cantidad,
            TOTAL=subtotal
        ))
    
    Detalles.objects.bulk_create(detalles_list)
    
    request.session['carrito'] = {}
    request.session['ultima_actividad_carrito'] = None
    request.session.modified = True
    
    return JsonResponse({'success': True, 'pedido_id': pedido.ID_REQUEST})

# ---------- VISTAS DE ADMINISTRACIÓN ----------
def is_admin(user):
    return user.is_staff or user.is_superuser

@login_required
@user_passes_test(is_admin)
def admin_catalogo(request):
    productos = Productos.objects.all()
    total_productos = productos.count()
    cliente = get_cliente_from_user(request.user)
    total_ventas = Pedidos.objects.count()  # o suma de totales
    context = {
        'productos': productos,
        'total_productos': total_productos,
        'cliente_nombre': cliente.NAME if cliente else request.user.username,
        'cliente_direccion': cliente.DIRECTION if cliente else 'Sin dirección',
        'total_ventas': total_ventas,
    }
    return render(request, 'catalogoadmin.html', context)

@login_required
@user_passes_test(is_admin)
def backup_database(request):
    db_path = str (settings.DATABASES['default']['NAME'])
    if not os.path.exists(db_path):
        raise Http404("Base de datos no encontrada")
    
    with open(db_path, 'rb') as f:
        response = HttpResponse(f.read(), content_type='application/x-sqlite3')
        response['Content-Disposition'] = f'attachment; filename="backup_{timezone.now().strftime("%Y%m%d_%H%M%S")}.sqlite3"'
        return response
    
def restore_database(request):
    if request.method == 'POST' and request.FILES.get('backup_file'):
        db_path = str(settings.DATABASES['default']['NAME'])
        subido = request.FILES['backup_file']
        
        try:
           
            connection.close()
            with open(db_path, 'wb') as f_destino:
                for chunk in subido.chunks():
                    f_destino.write(chunk)

            messages.success(request, "Base de datos sobrescrita con éxito.")
            return redirect('login_admin')
            
        except PermissionError:
            messages.error(request, "Error de acceso: El archivo está bloqueado por el servidor. Intenta detener el servidor y reemplazar el archivo manualmente o usa una herramienta de gestión de procesos.")
        except Exception as e:
            messages.error(request, f"Error: {str(e)}")
            
        return redirect('restore_database')
    
    return render(request, 'restore.html')

@login_required
def crear_producto(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        size = request.POST.get('size')
        tipo = request.POST.get('tipo') == '1'
        precio = request.POST.get('precio')
        stock = request.POST.get('stock')
        Productos.objects.create(
            PRODUCT_NAME=nombre,
            SIZE=size,
            TYPE=tipo,
            PRICE=precio,
            STOCK=stock
        )
        messages.success(request, f'Producto "{nombre}" creado.')
        return redirect('admin_catalogo')
    return render(request, 'formulario-productos.html')

@login_required
@transaction.atomic
def editar_producto(request, producto_id):
    producto = get_object_or_404(Productos.objects.select_for_update(), ID_PRODUCT=producto_id)
    if request.method == 'POST':
        producto.PRODUCT_NAME = request.POST.get('nombre')
        producto.SIZE = request.POST.get('size')
        producto.TYPE = request.POST.get('tipo') == '1'
        producto.PRICE = request.POST.get('precio')
        producto.STOCK = request.POST.get('stock')
        producto.save()
        messages.success(request, f'Producto "{producto.PRODUCT_NAME}" actualizado.')
        return redirect('admin_catalogo')
    return render(request, 'formulario-productos.html', {'producto': producto})

@login_required
def eliminar_producto(request, producto_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    try:
        producto = Productos.objects.get(ID_PRODUCT=producto_id)
        nombre = producto.PRODUCT_NAME
        producto.delete()
        return JsonResponse({'success': True, 'mensaje': f'Producto "{nombre}" eliminado.'})
    except Productos.DoesNotExist:
        return JsonResponse({'error': 'Producto no encontrado'}, status=404)

# ---------- CSRF TOKEN PARA PRUEBAS ----------
def get_csrf_token(request):
    return JsonResponse({'csrfToken': get_token(request)})

@login_required
def panel_ventas(request):
    # Opcional: restringir solo a administradores (staff)
    if not request.user.is_staff:
        raise Http404

    pedidos = Pedidos.objects.select_related('CLIENT').prefetch_related('detalles_set__PRODUCT').order_by('-DATE', '-TIME')
    
    datos_pedidos = []
    for pedido in pedidos:
        total = sum(detalle.TOTAL for detalle in pedido.detalles_set.all())
        datos_pedidos.append({
            'id': pedido.ID_REQUEST,
            'cliente_nombre': f"{pedido.CLIENT.NAME} {pedido.CLIENT.SURNAME}",
            'cliente_ci': pedido.CLIENT.CI,
            'fecha': pedido.DATE.strftime('%d/%m/%Y'),
            'hora': pedido.TIME.strftime('%H:%M'),
            'total': total,
        })

    context = {
        'pedidos': datos_pedidos,
    }
    return render(request, 'panelp.html', context)

@login_required
def detalle_pedido(request, pedido_id):
    # Solo administradores (staff) pueden ver detalles de pedidos
    if not request.user.is_staff:
        raise Http404

    pedido = get_object_or_404(
        Pedidos.objects.select_related('CLIENT').prefetch_related('detalles_set__PRODUCT'),
        ID_REQUEST=pedido_id
    )

    detalles_con_subtotal = []
    total_general = 0
    total_unidades = 0
    
    for detalle in pedido.detalles_set.all():
        cantidad = int(detalle.AMOUNT)
        subtotal = float(detalle.TOTAL)
        total_general += subtotal
        total_unidades += cantidad
        detalles_con_subtotal.append({
            'producto': detalle.PRODUCT,
            'cantidad': cantidad,
            'precio_unitario': float(detalle.PRODUCT.PRICE),
            'subtotal': subtotal,
        })

    context = {
        'pedido': pedido,
        'detalles': detalles_con_subtotal,
        'total_general': total_general,
        'cliente': pedido.CLIENT,
        'cantidad_productos': len(detalles_con_subtotal),
        'total_unidades': total_unidades,
    }
    return render(request, 'verpedido.html', context)