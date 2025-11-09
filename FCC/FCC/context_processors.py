# FCC/context_processors.py
from FCC.firebase_config import db

def usuario_context(request):
    usuario_data = None
    usuario_id = request.session.get("usuario_id")

    if usuario_id:
        try:
            doc = db.collection("usuarios").document(usuario_id).get()
            if doc.exists:
                usuario_data = doc.to_dict()
                usuario_data["id"] = usuario_id

                personaje_id = usuario_data.get("personaje_id")
                if personaje_id:
                    personaje_doc = db.collection("personajes").document(personaje_id).get()
                    if personaje_doc.exists:
                        usuario_data["personaje"] = personaje_doc.to_dict()
                        usuario_data["personaje"]["id"] = personaje_id
                    else:
                        usuario_data["personaje"] = None
                else:
                    usuario_data["personaje"] = None

        except Exception as e:
            print("Error al obtener usuario del context processor:", e)

    return {"current_user": usuario_data}
