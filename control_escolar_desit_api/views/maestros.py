from django.shortcuts import render, get_object_or_404
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from rest_framework import generics
from rest_framework import status
from django.contrib.auth.models import User, Group
import json
from rest_framework import filters

# --- CORRECCIÓN DE IMPORTACIONES ---
# Aseguramos que se importen desde donde realmente existen
from control_escolar_desit_api.serializers import UserSerializer, MaestroSerializer
from control_escolar_desit_api.models import Maestros
from .users import StandardResultsPagination, IsAdminOrMaestro 

# ====================================================
# VISTA DE LISTADO DE MAESTROS (GET /lista-maestros/)
# ====================================================

class MaestrosAll(generics.ListAPIView):
    """Lista de Maestros con paginación, ordenamiento y filtro."""
    permission_classes = (permissions.IsAuthenticated, IsAdminOrMaestro) 
    serializer_class = MaestroSerializer 
    queryset = Maestros.objects.filter(user__is_active=1).order_by("id") 
    pagination_class = StandardResultsPagination
    filter_backends = (filters.OrderingFilter, filters.SearchFilter)
    ordering_fields = ['id', 'id_trabajador', 'user__first_name', 'user__last_name']
    ordering = ['user__last_name']
    search_fields = ['user__first_name', 'user__last_name', 'id_trabajador', 'rfc']

    # Sobrescribimos el GET para mantener la deserialización de materias_json
    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        lista = response.data.get('results', []) 

        for maestro in lista:
            if isinstance(maestro, dict) and "materias_json" in maestro and maestro["materias_json"]:
                try:
                    # Deserializar el JSON string a una lista de Python/JS
                    maestro["materias_json"] = json.loads(maestro["materias_json"])
                except Exception:
                    maestro["materias_json"] = []
        
        response.data['results'] = lista
        return response

# ====================================================
# VISTA DE GESTIÓN INDIVIDUAL (CRUD)
# ====================================================

class MaestrosView(APIView):
    # Permitimos entrar a Admins y Maestros (para leer su propio perfil)
    #permission_classes = (permissions.IsAuthenticated, IsAdminOrMaestro)

    # 1. GET: Obtener maestro por ID (Necesario para el formulario de edición)
    def get(self, request):
        maestro_id = request.GET.get("id")
        if maestro_id:
            try:
                maestro = Maestros.objects.get(id=maestro_id)
                serializer = MaestroSerializer(maestro)
                data = serializer.data
                
                # Convertimos el string JSON de materias a una lista real para el Frontend
                if data.get("materias_json"):
                    try:
                        data["materias_json"] = json.loads(data["materias_json"])
                    except:
                        data["materias_json"] = []
                        
                return Response(data, status=200)
            except Maestros.DoesNotExist:
                return Response({"message": "Maestro no encontrado"}, 404)
        return Response({"message": "Falta el ID"}, 400)

    # 2. POST: Registrar nuevo usuario maestro (TU CÓDIGO ORIGINAL)
    @transaction.atomic
    def post(self, request, *args, **kwargs):
        user = UserSerializer(data=request.data)
        if user.is_valid():
            role = request.data['rol']
            first_name = request.data['first_name']
            last_name = request.data['last_name']
            email = request.data['email']
            password = request.data['password']
            existing_user = User.objects.filter(email=email).first()
            
            if existing_user:
                return Response({"message":"Username "+email+", is already taken"},400)
            
            user = User.objects.create( username = email,
                                        email = email,
                                        first_name = first_name,
                                        last_name = last_name,
                                        is_active = 1)
            user.save()
            user.set_password(password)
            user.save()
            
            group, created = Group.objects.get_or_create(name=role)
            group.user_set.add(user)
            user.save()
            
            # Create a profile for the user
            maestro = Maestros.objects.create(user=user,
                                            id_trabajador= request.data["id_trabajador"],
                                            fecha_nacimiento= request.data["fecha_nacimiento"],
                                            telefono= request.data["telefono"],
                                            rfc= request.data["rfc"].upper(),
                                            cubiculo= request.data["cubiculo"],
                                            area_investigacion= request.data["area_investigacion"],
                                            materias_json = json.dumps(request.data["materias_json"]))
            maestro.save()
            return Response({"maestro_created_id": maestro.id }, 201)
        return Response(user.errors, status=status.HTTP_400_BAD_REQUEST)


    @transaction.atomic
    def put(self, request, *args, **kwargs):
        if not request.user.groups.filter(name='administrador').exists():
            return Response({"message": "No tienes permisos para editar maestros"}, 403)

        try:
            maestro = Maestros.objects.get(id=request.data["id"])
        except Maestros.DoesNotExist:
            return Response({"message": "Maestro no encontrado"}, 404)

        maestro.id_trabajador = request.data.get("id_trabajador", maestro.id_trabajador)
        maestro.fecha_nacimiento = request.data.get("fecha_nacimiento", maestro.fecha_nacimiento)
        maestro.telefono = request.data.get("telefono", maestro.telefono)
        maestro.rfc = request.data.get("rfc", maestro.rfc)
        maestro.cubiculo = request.data.get("cubiculo", maestro.cubiculo)
        maestro.area_investigacion = request.data.get("area_investigacion", maestro.area_investigacion)
        
        if "materias_json" in request.data:
             if isinstance(request.data["materias_json"], list):
                 maestro.materias_json = json.dumps(request.data["materias_json"])
             else:
                 maestro.materias_json = request.data["materias_json"]
        
        maestro.save()
        
        user = maestro.user
        user.first_name = request.data.get("first_name", user.first_name)
        user.last_name = request.data.get("last_name", user.last_name)
        user.save()

        return Response({"message": "Maestro actualizado correctamente"}, 200)

    def delete(self, request, *args, **kwargs):
            if not request.user.groups.filter(name='administrador').exists():
                return Response({"message": "No tienes permisos para eliminar"}, 403)

            maestro_id = request.GET.get("id")
            try:
                maestro = Maestros.objects.get(id=maestro_id)
                maestro.user.delete()
                
                return Response({"message": "Maestro eliminado permanentemente"}, 200)
            except Maestros.DoesNotExist:
                return Response({"message": "Maestro no existe"}, 404)