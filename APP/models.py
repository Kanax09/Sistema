from django.db import models

class user_admin (models.Model):
    ADMIN_CI = models.CharField(max_length=20,primary_key=True ,verbose_name= "Cedula")
    PASSWORD = models.CharField(max_length=20, verbose_name= "Contraseña")

    class Meta:
        db_table="administrador"
        verbose_name ="administrador"

    def __str__(self) -> str:
        return self.ADMIN_CI

class Clientes (models.Model):
    CI = models.CharField(max_length=20,primary_key=True ,verbose_name= "Cedula")
    NAME = models.CharField(max_length=20,verbose_name="Nombre")
    SURNAME = models.CharField(max_length=20,verbose_name="Apellido")
    DIRECTION = models.CharField(max_length=20,verbose_name="Direccion")
    BIRTHDATE = models.DateField(verbose_name="Fecha_nacimiento")
    USERNAME = models.CharField(max_length=20,verbose_name="Usuario")
    PASSWORD = models.CharField(max_length=20,verbose_name="Clave")
    
    class Meta:
        db_table="Cliente"
        verbose_name ="Cliente"

    def __str__(self) -> str:
        return self.NAME
    

class Productos (models.Model):
    ID_PRODUCT = models.AutoField(primary_key=True, verbose_name="ID_Producto")
    PRODUCT_NAME = models.CharField(max_length=20,verbose_name="Nombre_producto")
    SIZE= models.CharField(max_length=20,verbose_name="Tamaño")
    TYPE = models.BooleanField(verbose_name="Presentacion")
    PRICE = models.CharField(max_length=20,verbose_name="Precio")
    STOCK = models.IntegerField(max_length=20,verbose_name="Cantidad")
   
    
    class Meta:
        db_table="Producto"
        verbose_name ="Producto"

    def __str__(self) -> str:
        return self.PRODUCT_NAME
    
class Pedidos (models.Model):
    ID_REQUEST = models.AutoField(primary_key=True, verbose_name="ID_Pedido")
    CLIENT = models.ForeignKey(Clientes,on_delete=models.CASCADE,verbose_name="Cliente")
    DATE= models.DateField(max_length=20,verbose_name="Fecha_pedido")
    TIME = models.TimeField(max_length=20,verbose_name="Etiqueta")
   
    
    class Meta:
        db_table="Pedido"
        verbose_name ="Pedido"

    def __int__(self) -> int:
        return self.ID_REQUEST
    
class Detalles (models.Model):
    ID_DETAILS = models.AutoField(primary_key=True, verbose_name="ID_Pedido")
    ID_PEDIDO = models.ForeignKey(Pedidos,on_delete=models.CASCADE,verbose_name="Pedido")
    PRODUCT= models.ForeignKey(Productos,on_delete=models.CASCADE,verbose_name="Producto")
    AMOUNT = models.CharField(max_length=20,verbose_name="Cantidad")
    TOTAL = models.IntegerField(max_length=20,verbose_name="Monto_total")
   
    
    class Meta:
        db_table="Detalles"
        verbose_name ="Detalles"

    def __int__(self) -> int:
        return self.ID_DETAILS