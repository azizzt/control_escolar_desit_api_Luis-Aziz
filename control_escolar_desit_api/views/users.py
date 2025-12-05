from django.db.models import *
from django.db import transaction
from control_escolar_desit_api.serializers import UserSerializer, AdminSerializer, AlumnoSerializer, MaestroSerializer
from control_escolar_desit_api.models import *
from rest_framework import permissions
from rest_framework import generics
from rest_framework import status
from rest_framework.response import Response
from django.contrib.auth.models import Group
from django.shortcuts import get_object_or_404
import json
from rest_framework.pagination import PageNumberPagination
from rest_framework import filters

# ====================================================
#  CONFIGURACIÓN GLOBAL (PAGINACIÓN Y PERMISOS)
# ====================================================

# Paginación estándar para todas las tablas
class StandardResultsPagination(PageNumberPagination):
    page_size = 10 
    page_size_query_param = 'page_size' 
    max_page_size = 100 

# Permiso: Solo Administrador
class IsAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.groups.filter(name='administrador').exists()

# Permiso: Admin o Maestro
class IsAdminOrMaestro(permissions.BasePermission):
    def has_permission(self, request, view):
        user_groups = request.user.groups.values_list('name', flat=True)
        return 'administrador' in user_groups or 'maestro' in user_groups

# Permiso: Admin, Maestro o Alumno
class IsAdminMaestroOrAlumno(permissions.BasePermission):
    def has_permission(self, request, view):
        user_groups = request.user.groups.values_list('name', flat=True)
        return 'administrador' in user_groups or 'maestro' in user_groups or 'alumno' in user_groups

# ====================================================
#  VISTAS DE PERFIL Y ESTADÍSTICAS
# ====================================================

# Obtener perfil del usuario logueado (Cualquier rol)
class UserProfileView(generics.RetrieveAPIView): 
    permission_classes = (permissions.IsAuthenticated,)
    
    def get(self, request, *args, **kwargs):
        user = request.user 
        rol_name = user.groups.first().name if user.groups.exists() else None
        
        if rol_name == 'administrador':
            try:
                admin = Administradores.objects.get(user=user)
                data = AdminSerializer(admin).data
                data['rol'] = 'administrador'
                return Response(data, 200)
            except Administradores.DoesNotExist:
                pass
        elif rol_name == 'maestro':
            try:
                maestro = Maestros.objects.get(user=user)
                data = MaestroSerializer(maestro).data
                data['rol'] = 'maestro'
                return Response(data, 200)
            except Maestros.DoesNotExist:
                pass
        elif rol_name == 'alumno':
            try:
                alumno = Alumnos.objects.get(user=user)
                data = AlumnoSerializer(alumno).data
                data['rol'] = 'alumno'
                return Response(data, 200)
            except Alumnos.DoesNotExist:
                pass
        
        return Response({"message": "Perfil no encontrado"}, 404)

class TotalUsers(generics.RetrieveAPIView):
    permission_classes = (permissions.IsAuthenticated,)
    def get(self, request, *args, **kwargs):
        return Response({
            "admins": Administradores.objects.filter(user__is_active=True).count(),
            "maestros": Maestros.objects.filter(user__is_active=True).count(),
            "alumnos": Alumnos.objects.filter(user__is_active=True).count(),
        }, 200)

# ====================================================
#  VISTAS DE ADMINISTRADORES
# ====================================================

# LISTA AVANZADA (Paginación + Search + Sort)
class AdminAll(generics.ListAPIView):
    permission_classes = (permissions.IsAuthenticated, IsAdmin) 
    serializer_class = AdminSerializer 
    queryset = Administradores.objects.filter(user__is_active=1).order_by("id") 
    pagination_class = StandardResultsPagination
    filter_backends = (filters.OrderingFilter, filters.SearchFilter)
    ordering_fields = ['id', 'user__first_name', 'user__last_name', 'clave_admin'] 
    ordering = ['user__last_name']
    search_fields = ['user__first_name', 'user__last_name', 'clave_admin', 'rfc']

# CRUD (Crear, Editar, Eliminar) - Mantenemos tu lógica original
class AdminView(generics.CreateAPIView):
    def get(self, request, *args, **kwargs):
        admin = get_object_or_404(Administradores, id = request.GET.get("id"))
        return Response(AdminSerializer(admin).data, 200)

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        user = UserSerializer(data=request.data)
        if user.is_valid():
            email = request.data['email']
            if User.objects.filter(email=email).exists():
                return Response({"message":f"El email {email} ya está registrado"}, 400)

            user = User.objects.create( 
                username = email, email = email, 
                first_name = request.data['first_name'], 
                last_name = request.data['last_name'], is_active = 1
            )
            user.set_password(request.data['password'])
            user.save()
            
            group, _ = Group.objects.get_or_create(name='administrador')
            group.user_set.add(user)
            
            admin = Administradores.objects.create(
                user=user,
                clave_admin= request.data["clave_admin"],
                telefono= request.data["telefono"],
                rfc= request.data["rfc"].upper(),
                edad= request.data["edad"],
                ocupacion= request.data["ocupacion"]
            )
            return Response({"id": admin.id}, 201)
        return Response(user.errors, 400)

    @transaction.atomic
    def put(self, request, *args, **kwargs):
        admin = get_object_or_404(Administradores, id=request.data["id"])
        admin.clave_admin = request.data["clave_admin"]
        admin.telefono = request.data["telefono"]
        admin.rfc = request.data["rfc"]
        admin.edad = request.data["edad"]
        admin.ocupacion = request.data["ocupacion"]
        admin.save()
        admin.user.first_name = request.data["first_name"]
        admin.user.last_name = request.data["last_name"]
        admin.user.save()
        return Response(AdminSerializer(admin).data, 200)

    @transaction.atomic
    def delete(self, request, *args, **kwargs):
        admin = get_object_or_404(Administradores, id=request.GET.get("id"))
        if admin.user.id == request.user.id:
            return Response({"message": "No puedes eliminarte a ti mismo"}, 400)
        admin.user.delete()
        return Response({"message": "Administrador eliminado"}, 200)