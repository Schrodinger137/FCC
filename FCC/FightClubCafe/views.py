from django.shortcuts import render, redirect
from django.http import JsonResponse
from FCC.firebase_config import db, bucket
from django.contrib import messages
from django.core.files.storage import default_storage
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import uuid

# Create your views here.


def offline(request):
    return render(request, 'offline.html', status=200)

##################
## AUTH SECTION ##
##################


def verify_session(request):
    usuario_id = request.session.get("usuario_id")
    if not usuario_id:
        return redirect("login")
    return None


def verify_admin(request):
    usuario_id = request.session.get("usuario_id")
    if not usuario_id:
        return redirect("login")

    rol = request.session.get("usuario_rol")
    print("ROL ACTUAL:", rol)

    if rol not in ["admin", "Admin"]:
        print("Acceso denegado")
        return redirect("index")

    return None


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
        request.session["usuario_rol"] = usuario.get("rol")

        if usuario.get("rol") == "admin":
            return redirect("administrator")
        else:
            return redirect("index")

    return render(request, "auth/login.html")


def logout(request):
    request.session.flush()
    return redirect("login")


#####################
## GENERAL SECTION ##
#####################


def index(request):

    docs = db.collection("personajes").stream()
    personajes = [{**doc.to_dict(), "id": doc.id} for doc in docs]
    
    docs = db.collection('cafe').stream()
    items = [{**doc.to_dict(), "id": doc.id} for doc in docs]
    
    usuarios_docs = db.collection("usuarios").stream()
    usuarios_count = sum(1 for _ in usuarios_docs)

    context = {
        "personajes": personajes,
        'items':items,
        'usuarios_count':usuarios_count,
        }

    return render(request, "principal/index.html", context)


def characters(request):

    docs = db.collection("personajes").stream()
    personajes = [{**doc.to_dict(), "id": doc.id} for doc in docs]
    
    docs = db.collection("cafe").stream()
    items = [{**doc.to_dict(), "id": doc.id} for doc in docs]

    context = {
        "personajes": personajes,
        'items':items
        }

    return render(request, "principal/characters.html", context)


def items(request):

    docs = db.collection("cafe").stream()
    items = [{**doc.to_dict(), "id": doc.id} for doc in docs]

    context = {"items": items}

    return render(request, "principal/items.html", context)


def chat(request):
    
    return render(request, 'principal/chat.html')


def account(request):
    redireccion = verify_session(request)
    if redireccion:
        return redireccion

    usuario_id = request.session.get("usuario_id")
    doc = db.collection("usuarios").document(usuario_id).get()
    usuario = doc.to_dict()
    return render(request, "auth/account.html", {"usuario": usuario})


def administrator(request):
    verify = verify_admin(request)
    if verify:
        return verify

    personajes_docs = list(db.collection("personajes").limit(2).stream())
    personajes_img_1 = None
    personajes_img_2 = None

    if personajes_docs:
        personaje1 = personajes_docs[0].to_dict()
        personajes_img_1 = personaje1.get("imagen")

        if len(personajes_docs) > 1:
            personaje2 = personajes_docs[1].to_dict()
            personajes_img_2 = personaje2.get("imagen")

    cafe_docs = list(db.collection("cafe").limit(1).stream())
    cafe_img = None
    if cafe_docs:
        item = cafe_docs[0].to_dict()
        cafe_img = item.get("imagen")

    context = {
        "personajes_img": personajes_img_1,
        "personajes_img_2": personajes_img_2,
        "cafe_img": cafe_img,
    }

    return render(request, "administrator/administrator.html", context)


#########################
## ADMIN USERS SECTION ##
#########################


def admin_users(request):

    verify = verify_admin(request)
    if verify:
        return verify

    usuarios = []
    usuarios_docs = db.collection("usuarios").stream()
    
    docs = db.collection("personajes").stream()
    personajes = [{**doc.to_dict(), "id": doc.id} for doc in docs]

    for doc in usuarios_docs:
        usuario = doc.to_dict()
        usuario["id"] = doc.id
        if usuario.get("eliminado"):
            continue

        personaje_id = usuario.get("personaje_id")
        if personaje_id:
            personaje_doc = db.collection("personajes").document(personaje_id).get()
            usuario["personaje"] = (
                personaje_doc.to_dict() if personaje_doc.exists else None
            )
        else:
            usuario["personaje"] = None

        usuarios.append(usuario)

    context = {
        "usuarios": usuarios,
        'personajes':personajes,
        }

    return render(request, "administrator/admin_users.html", context)


def create_user(request):

    # Proteger endpoint
    if request.session.get("usuario_rol") not in ["admin", "Admin"]:
        return JsonResponse({"error": "No autorizado"}, status=403)

    if request.method != "POST":
        return JsonResponse({"error": "Método no permitido"}, status=405)

    nombre = request.POST.get("nombre")
    correo = request.POST.get("correo")
    password = request.POST.get("password")
    personaje_id = request.POST.get("personaje_id")

    if not nombre or not correo or not password:
        return JsonResponse({"error": "Todos los campos son obligatorios"}, status=400)

    try:
        nuevo = db.collection("usuarios").add({
            "nombre": nombre,
            "correo": correo,
            "contraseña": password,
            "personaje_id": personaje_id,
            "rol": "usuario",
            "eliminado": False,
        })

        return JsonResponse({"mensaje": "Usuario creado correctamente"})
    
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


def delete_user(request, user_id):

    verify = verify_admin(request)
    if verify:
        return verify

    if request.method == 'POST':
        db.collection('usuarios').document(user_id).delete()
        return redirect('admin_users')

    return redirect('admin_users')



###############################
## ADMIN CHARACTERS SECTIONS ##
###############################


def admin_characters(request):

    verify = verify_admin(request)
    if verify:
        return verify

    personajes_docs = db.collection("personajes").stream()
    personajes = []

    usuarios_docs = db.collection("usuarios").stream()
    usuarios = [doc.to_dict() for doc in usuarios_docs]

    for doc in personajes_docs:
        personaje_data = doc.to_dict()
        personaje_id = doc.id

        cantidad_usuarios = sum(
            1 for u in usuarios if u.get("personaje_id") == personaje_id
        )

        personaje_data["id"] = personaje_id
        personaje_data["jugadores_asociados"] = cantidad_usuarios

        personajes.append(personaje_data)

    return render(
        request, "administrator/admin_character.html", {"personajes": personajes}
    )


def create_character(request):

    verify = verify_admin(request)
    if verify:
        return verify

    if request.method == "POST":

        nombre = request.POST.get("nombre")
        descripcion = request.POST.get("descripcion")
        imagen_url = request.POST.get("imagen")
        dano = request.POST.get("dano")
        velocidad = request.POST.get("velocidad")

        new_character = {
            "nombre": nombre,
            "descripcion": descripcion,
            "imagen": imagen_url,
            "dano": dano,           # se queda string
            "velocidad": velocidad  # se queda string
        }

        _, ref = db.collection("personajes").add(new_character)

        return JsonResponse({
            "mensaje": "Personaje creado correctamente",
            "id": ref.id,
            "imagen_url": imagen_url
        })

    return JsonResponse({"error": "Método no permitido"}, status=400)



def edit_character(request, character_id):

    verify = verify_admin(request)
    if verify:
        return verify

    if request.method == "POST":

        nombre = request.POST.get("nombre")
        descripcion = request.POST.get("descripcion")
        imagen_url = request.POST.get("imagen")
        dano = request.POST.get("dano")
        velocidad = request.POST.get("velocidad")

        db.collection("personajes").document(character_id).update({
            "nombre": nombre,
            "descripcion": descripcion,
            "imagen": imagen_url,
            "dano": dano,           # string OK
            "velocidad": velocidad  # string OK
        })

        return JsonResponse({
            "mensaje": "Personaje actualizado correctamente",
            "id": character_id,
            "imagen": imagen_url
        })

    return JsonResponse({"error": "Método no permitido"}, status=400)




def delete_character(request, character_id):

    verify = verify_admin(request)
    if verify:
        return verify

    if request.method == 'POST':
        db.collection('personajes').document(character_id).delete()
        return redirect('admin_characters')

    return redirect('admin_characters')


#########################
## ADMIN ITEMS SECTION ##
#########################


def admin_items(request):

    verify = verify_admin(request)
    if verify:
        return verify

    items_docs = db.collection("cafe").stream()
    items = []

    for doc in items_docs:
        item_data = doc.to_dict()
        item_id = doc.id

        item_data["id"] = item_id
        items.append(item_data)

    return render(request, "administrator/admin_items.html", {"items": items})


def create_item(request):

    verify = verify_admin(request)
    if verify:
        return verify

    if request.method == "POST":

        nombre = request.POST.get("nombre")
        duracion = request.POST.get("duracion")
        aumentoDano = request.POST.get("aumentoDano")
        aumentoVelocidad = request.POST.get("aumentoVelocidad")
        imagen_url = request.POST.get("imagen")  # <-- URL directa

        new_item = {
            "nombre": nombre,
            "duracion": duracion,
            "aumentoDano": aumentoDano,
            "aumentoVelocidad": aumentoVelocidad,
            "imagen": imagen_url,
        }

        _, ref = db.collection("cafe").add(new_item)

        return JsonResponse({
            "mensaje": "Item creado correctamente",
            "id": ref.id,
            "imagen_url": imagen_url
        })

    return JsonResponse({"error": "Método no permitido"}, status=400)


def edit_item(request, item_id):

    verify = verify_admin(request)
    if verify:
        return verify

    if request.method == "POST":
        nombre = request.POST.get("nombre")
        duracion = request.POST.get("duracion")
        aumentoDano = request.POST.get("aumentoDano")
        aumentoVelocidad = request.POST.get("aumentoVelocidad")
        imagen_url = request.POST.get("imagen")

        db.collection("cafe").document(item_id).update({
            "nombre": nombre,
            "duracion": duracion,
            "aumentoDano": aumentoDano,
            "aumentoVelocidad": aumentoVelocidad,
            "imagen": imagen_url,
        })

        return JsonResponse({
            "mensaje": "Item actualizado correctamente",
            "id": item_id,
            "imagen": imagen_url
        })

    return JsonResponse({"error": "Método no permitido"}, status=400)



def delete_item(request, item_id):

    verify = verify_admin(request)
    if verify:
        return verify

    if request.method == "POST":
        db.collection("cafe").document(item_id).delete()
        return redirect('admin_items')

    return redirect('admin_items')
