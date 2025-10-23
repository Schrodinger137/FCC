from django.shortcuts import render, redirect
from django.http import JsonResponse
from FCC.firebase_config import db
from django.contrib import messages


# Create your views here.
def index(request):
    usuario_id = request.session.get('usuario_id')
    if not usuario_id:
        return redirect('login')

    doc = db.collection('usuarios').document(usuario_id).get()
    usuario = doc.to_dict()

    return render(request, "principal/index.html", {'usuario':usuario})

def signin(request):
    if request.method == "POST":
        nombre = request.POST.get("nombre")
        correo = request.POST.get("correo")
        password = request.POST.get("password")
        personaje_id = request.POST.get("personaje")

        db.collection("usuarios").add(
            {
                "nombre": nombre,
                "correo": correo,
                "contraseña": password,
                "personaje_id": personaje_id,
            }
        )
        return redirect("login")

    docs = db.collection("personajes").stream()
    personajes = [{**doc.to_dict(), "id": doc.id} for doc in docs]
    return render(request, "auth/signin.html", {"personajes": personajes})

def login(request):
    if request.method == "POST":
        correo = request.POST.get("correo")
        contraseña = request.POST.get("contraseña")

        usuarios_ref = db.collection("usuarios")
        query = usuarios_ref.where("correo", "==", correo).stream()
        usuario = None

        for doc in query:
            usuario = doc.to_dict()
            usuario["id"] = doc.id
            break

        if usuario is None:
            messages.error(request, "No existe una cuenta con ese correo", correo)
            return render(request, "auth/login.html")

        if usuario["contraseña"] != contraseña:
            messages.error(request, "Contraseña incorrecta")
            return render(request, "auth/login.html")

        request.session["usuario_id"] = usuario["id"]
        request.session["usuario_nombre"] = usuario["nombre"]

        return redirect("/")

    return render(request, "auth/login.html")

def logout(request):
    request.session.flush()
    return redirect('login')

def account(request):
    usuario_id = request.session.get('usuario_id')
    if not usuario_id:
        return redirect('login')

    doc = db.collection('usuarios').document(usuario_id).get()
    usuario = doc.to_dict()
    return render (request, 'auth/account.html', {'usuario':usuario})


def administrator(request):
    return render(request, "administrator/administrator.html")


def admin_users(request):
    docs = db.collection("usuarios").stream()
    usuarios = [{**doc.to_dict(), "id": doc.id} for doc in docs]
    return render(request, "administrator/admin_users.html", {"usuarios": usuarios})


def admin_characters(request):
    return render(request, "administrator/admin_character.html")


def listar_usuarios(request):
    docs = db.collection("usuarios").stream()
    usuarios = [{**doc.to_dict(), "id": doc.id} for doc in docs]
    return JsonResponse({"usuarios": usuarios})


def form_usuario(request):
    if request.method == "GET":
        return render(request, "principal/form.html")
    elif request.method == "POST":
        nombre = request.POST.get("nombre")
        edad = request.POST.get("edad")

        if not nombre or not edad:
            return JsonResponse({"error": "Faltan datos"}, status=400)

        db.collection("usuarios").add({"nombre": nombre, "edad": int(edad)})

        return JsonResponse({"mensaje": "Usuario agregado correctamente"})
