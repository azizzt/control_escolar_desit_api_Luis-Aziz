from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from control_escolar_desit_api.views import users, alumnos, maestros, auth, materias_view # <--- IMPORTAR materias_view

urlpatterns = [
    # --- GESTIÓN (CRUD) ---
    path('admin/', users.AdminView.as_view()),
    path('alumnos/', alumnos.AlumnosView.as_view()),
    path('maestros/', maestros.MaestrosView.as_view()),
    
    # --- LISTADOS AVANZADOS ---
    path('lista-admins/', users.AdminAll.as_view()), 
    path('lista-maestros/', maestros.MaestrosAll.as_view()), 
    path('lista-alumnos/', alumnos.AlumnosAll.as_view()), 

    # --- MATERIAS ---
    path('materias/', materias_view.MateriasView.as_view()), # CRUD (Post, Put, Delete, Get one)
    path('lista-materias/', materias_view.MateriasList.as_view()), # Listado (Page, Sort, Filter)
    
    # --- SISTEMA ---
    path('me/', users.UserProfileView.as_view()), # Perfil
    path('total-usuarios/', users.TotalUsers.as_view()),
    path('login/', auth.CustomAuthToken.as_view()),
    path('logout/', auth.Logout.as_view()),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)