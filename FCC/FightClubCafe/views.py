from django.shortcuts import render
from django.http import JsonResponse
from FCC.firebase_config import db

# Create your views here.
def index(request):
    return render(request, 'principal/index.html')

def crear_usuario(request):
    data = {'nombre': 'Carlos', 'edad': 25}
    db.collection('usuarios').add(data)
    return JsonResponse({'mensaje': 'Usuario agregado'})

def listar_usuarios(request):
    docs = db.collection('usuarios').stream()
    usuarios = [{**doc.to_dict(), "id": doc.id} for doc in docs]
    return JsonResponse({"usuarios": usuarios})