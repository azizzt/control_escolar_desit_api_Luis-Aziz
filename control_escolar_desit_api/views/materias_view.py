from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import permissions, generics, status, filters
from rest_framework.response import Response
import json

# IMPORTANTE: Agregamos 'Maestros' a los imports
from control_escolar_desit_api.models import Materias, Maestros
from control_escolar_desit_api.serializers import MateriaSerializer
from .users import StandardResultsPagination, IsAdminMaestroOrAlumno, IsAdminOrMaestro

# ====================================================
# LISTA DE MATERIAS (GET /lista-materias/)
# ====================================================
class MateriasList(generics.ListAPIView):
    # Visible para Admin, Maestro y Alumno
    permission_classes = (permissions.IsAuthenticated, IsAdminMaestroOrAlumno)
    serializer_class = MateriaSerializer
    queryset = Materias.objects.all().order_by("id")
    pagination_class = StandardResultsPagination
    filter_backends = (filters.OrderingFilter, filters.SearchFilter)
    
    # Ordenar por NRC o Nombre
    ordering_fields = ['id', 'nrc', 'nombre']
    ordering = ['nombre']
    
    # Buscar por NRC, Nombre o Programa
    search_fields = ['nrc', 'nombre', 'programa_educativo']

    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        lista = response.data.get('results', [])
        for materia in lista:
            if "dias" in materia and isinstance(materia["dias"], str):
                try:
                    materia["dias"] = json.loads(materia["dias"])
                except:
                    materia["dias"] = []
        response.data['results'] = lista
        return response

# ====================================================
# GESTIÓN DE MATERIAS (CRUD)
# ====================================================
class MateriasView(generics.CreateAPIView):
    permission_classes = (permissions.IsAuthenticated, IsAdminOrMaestro)

    # OBTENER UNA MATERIA POR ID
    def get(self, request, *args, **kwargs):
        materia = get_object_or_404(Materias, id=request.GET.get("id"))
        data = MateriaSerializer(materia).data
        
        # Parsear dias si es string
        if isinstance(data.get("dias"), str):
            try:
                data["dias"] = json.loads(data["dias"])
            except:
                data["dias"] = []
        return Response(data, 200)

    # REGISTRAR MATERIA
    @transaction.atomic
    def post(self, request, *args, **kwargs):
        # Validar si ya existe el NRC
        if Materias.objects.filter(nrc=request.data.get("nrc")).exists():
            return Response({"message": "El NRC ya existe."}, 400)

        # Manejo de JSON para 'dias'
        dias_json = request.data.get("dias", [])
        if isinstance(dias_json, list):
            dias_json = json.dumps(dias_json)

        # ---> NUEVO: Buscar la instancia del Maestro por ID
        profesor_id = request.data.get("profesor") # El frontend envía el ID (ej: 15)
        profesor_instance = None
        if profesor_id:
            try:
                profesor_instance = Maestros.objects.get(id=profesor_id)
            except Maestros.DoesNotExist:
                return Response({"message": "El profesor seleccionado no existe"}, 400)

        try:
            materia = Materias.objects.create(
                nrc=request.data["nrc"],
                nombre=request.data["nombre"],
                seccion=request.data["seccion"],
                dias=dias_json,
                hora_inicio=request.data["hora_inicio"],
                hora_fin=request.data["hora_fin"],
                salon=request.data["salon"],
                programa_educativo=request.data["programa_educativo"],
                # ---> NUEVO: Agregamos créditos y profesor
                creditos=request.data.get("creditos", 1), # Default 1 si no viene
                profesor=profesor_instance
            )
            return Response({"id": materia.id, "message": "Materia creada correctamente"}, 201)
        except Exception as e:
            return Response({"message": str(e)}, 400)

    # ACTUALIZAR MATERIA
    @transaction.atomic
    def put(self, request, *args, **kwargs):
        try:
            materia = Materias.objects.get(id=request.data["id"])
            
            # Validar NRC único (si cambió)
            new_nrc = request.data.get("nrc")
            if new_nrc and new_nrc != materia.nrc:
                if Materias.objects.filter(nrc=new_nrc).exists():
                    return Response({"message": "El NRC ya está ocupado por otra materia."}, 400)

            materia.nrc = request.data.get("nrc", materia.nrc)
            materia.nombre = request.data.get("nombre", materia.nombre)
            materia.seccion = request.data.get("seccion", materia.seccion)
            materia.hora_inicio = request.data.get("hora_inicio", materia.hora_inicio)
            materia.hora_fin = request.data.get("hora_fin", materia.hora_fin)
            materia.salon = request.data.get("salon", materia.salon)
            materia.programa_educativo = request.data.get("programa_educativo", materia.programa_educativo)
            
            # ---> NUEVO: Actualizar Créditos
            materia.creditos = request.data.get("creditos", materia.creditos)

            # ---> NUEVO: Actualizar Profesor
            # Verificamos si en el request viene el campo 'profesor'
            if "profesor" in request.data:
                profesor_id = request.data.get("profesor")
                if profesor_id:
                    try:
                        materia.profesor = Maestros.objects.get(id=profesor_id)
                    except Maestros.DoesNotExist:
                        return Response({"message": "El profesor no existe"}, 400)
                else:
                    # Si mandan null o vacío, desasignamos al profe
                    materia.profesor = None

            if "dias" in request.data:
                dias_data = request.data["dias"]
                if isinstance(dias_data, list):
                    materia.dias = json.dumps(dias_data)
                else:
                    materia.dias = dias_data
            
            materia.save()
            return Response({"message": "Materia actualizada"}, 200)
        except Materias.DoesNotExist:
            return Response({"message": "La materia no existe"}, 404)

    # ELIMINAR MATERIA
    @transaction.atomic
    def delete(self, request, *args, **kwargs):
        try:
            materia = Materias.objects.get(id=request.GET.get("id"))
            materia.delete()
            return Response({"message": "Materia eliminada"}, 200)
        except Materias.DoesNotExist:
            return Response({"message": "La materia no existe"}, 404)