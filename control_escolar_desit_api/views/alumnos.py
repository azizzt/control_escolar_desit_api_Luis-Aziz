from django.db.models import *
from django.db import transaction
from control_escolar_desit_api.serializers import UserSerializer, AlumnoSerializer
from control_escolar_desit_api.models import *
from rest_framework import permissions, generics, status, filters
from rest_framework.response import Response
from django.contrib.auth.models import Group
from django.shortcuts import get_object_or_404
# Importamos la configuración desde users.py
from .users import StandardResultsPagination, IsAdminMaestroOrAlumno

# LISTA AVANZADA (Paginación + Search + Sort)
class AlumnosAll(generics.ListAPIView):
    permission_classes = (permissions.IsAuthenticated, IsAdminMaestroOrAlumno) 
    serializer_class = AlumnoSerializer 
    queryset = Alumnos.objects.filter(user__is_active=1).order_by("id") 
    pagination_class = StandardResultsPagination
    filter_backends = (filters.OrderingFilter, filters.SearchFilter)
    ordering_fields = ['id', 'matricula', 'user__first_name', 'user__last_name']
    ordering = ['user__last_name']
    search_fields = ['user__first_name', 'user__last_name', 'matricula', 'curp']

# CRUD (Crear, Editar, Eliminar)
class AlumnosView(generics.CreateAPIView):
    def get(self, request, *args, **kwargs):
        alumno = get_object_or_404(Alumnos, id=request.GET.get("id"))
        return Response(AlumnoSerializer(alumno).data, 200)

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        user = UserSerializer(data=request.data)
        if user.is_valid():
            if User.objects.filter(email=request.data['email']).exists():
                return Response({"message": "Email ya registrado"}, 400)

            user = User.objects.create(
                username=request.data['email'], email=request.data['email'],
                first_name=request.data['first_name'], last_name=request.data['last_name'], is_active=1
            )
            user.set_password(request.data['password'])
            user.save()
            Group.objects.get_or_create(name='alumno')[0].user_set.add(user)

            alumno = Alumnos.objects.create(
                user=user, matricula=request.data["matricula"], curp=request.data["curp"].upper(),
                rfc=request.data["rfc"].upper(), fecha_nacimiento=request.data["fecha_nacimiento"],
                edad=request.data["edad"], telefono=request.data["telefono"],
                ocupacion=request.data["ocupacion"]
            )
            return Response({"id": alumno.id}, 201)
        return Response(user.errors, 400)

    @transaction.atomic
    def put(self, request, *args, **kwargs):
        alumno = get_object_or_404(Alumnos, id=request.data["id"])
        alumno.matricula = request.data["matricula"]
        alumno.curp = request.data["curp"]
        alumno.rfc = request.data["rfc"]
        alumno.fecha_nacimiento = request.data["fecha_nacimiento"]
        alumno.edad = request.data["edad"]
        alumno.telefono = request.data["telefono"]
        alumno.ocupacion = request.data["ocupacion"]
        alumno.save()
        alumno.user.first_name = request.data["first_name"]
        alumno.user.last_name = request.data["last_name"]
        alumno.user.save()
        return Response(AlumnoSerializer(alumno).data, 200)

    @transaction.atomic
    def delete(self, request, *args, **kwargs):
        alumno = get_object_or_404(Alumnos, id=request.GET.get("id"))
        alumno.user.delete()
        return Response({"message": "Alumno eliminado"}, 200)