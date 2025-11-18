from django.shortcuts import render, redirect
from django.http import JsonResponse
from FCC.firebase_config import db, bucket
from django.contrib import messages
from django.core.files.storage import default_storage
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import uuid

# Create your views here.

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

    context = {
        "personajes": personajes,
        'items':items,
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
        "personajes_img_2": personajes_img_2,   # ← NUEVA
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

    return render(request, "administrator/admin_users.html", {"usuarios": usuarios})


def delete_users(request):

    # Nunca redirigir en un fetch()
    if request.session.get("usuario_rol") not in ["admin", "Admin"]:
        return JsonResponse({"error": "No autorizado"}, status=403)

    if request.method != "POST":
        return JsonResponse({"error": "Método no permitido"}, status=405)

    usuario_id = request.POST.get("usuario_id")

    try:
        usuario_ref = db.collection("usuarios").document(usuario_id)
        usuario_ref.update({"eliminado": True})

        return JsonResponse({"mensaje": "Usuario marcado como eliminado"})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)



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
        return JsonResponse(
            {"error": "No tienes permisos para esta acción."}, status=403
        )

    if request.method != "POST":
        return JsonResponse({"error": "Método no permitido."}, status=405)

    nombre = request.POST.get("nombre")
    descripcion = request.POST.get("descripcion")
    imagen = request.FILES.get("imagen")

    if not nombre or not descripcion:
        return JsonResponse(
            {"error": "Nombre y descripción son obligatorios."}, status=400
        )

    try:
        imagen_url = None
        if imagen:
            imagen_nombre = f"personajes/{uuid.uuid4()}_{imagen.name}"
            blob = bucket.blob(imagen_nombre)
            blob.upload_from_file(imagen, content_type=imagen.content_type)
            blob.make_public()
            imagen_url = blob.public_url

        personaje_ref = db.collection("personajes").add(
            {
                "nombre": nombre,
                "descripcion": descripcion,
                "imagen_url": imagen_url,
            }
        )

        return JsonResponse(
            {
                "mensaje": "Personaje creado correctamente.",
                "id": personaje_ref[1].id,
                "imagen_url": imagen_url,
            }
        )

    except Exception as e:
        return JsonResponse(
            {"error": f"Error al crear personaje: {str(e)}"}, status=500
        )


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
