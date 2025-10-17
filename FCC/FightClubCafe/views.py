from django.shortcuts import render
from django.http import JsonResponse
from FCC.firebase_config import db

# Create your views here.
def index(request):
    return render(request, 'principal/index.html')


def administrator(request):
    return render(request, 'administrator/administrator.html')

def admin_users(request):    
    docs = db.collection('usuarios').stream()
    usuarios = [{**doc.to_dict(), 'id':doc.id} for doc in docs]
    return render(request, 'administrator/admin_users.html', {'usuarios':usuarios})

def admin_characters(request):
    return render(request, 'administrator/admin_character.html')

def listar_usuarios(request):
    docs = db.collection('usuarios').stream()
    usuarios = [{**doc.to_dict(), "id": doc.id} for doc in docs]
    return JsonResponse({"usuarios": usuarios})

def form_usuario(request):
    if request.method == 'GET':
        return render(request, 'principal/form.html')
    elif request.method == 'POST':
        nombre = request.POST.get('nombre')
        edad = request.POST.get('edad')

        if not nombre or not edad:
            return JsonResponse({'error': 'Faltan datos'}, status=400)
        
        db.collection('usuarios').add({
            'nombre': nombre,
            'edad': int(edad)
        })

        return JsonResponse({'mensaje': 'Usuario agregado correctamente'})