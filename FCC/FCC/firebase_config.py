import firebase_admin
from firebase_admin import credentials, firestore, auth, storage

# Ruta a tu archivo JSON
cred = credentials.Certificate("FCC/fightclubcafe-e852c-firebase-adminsdk-fbsvc-a7582439b5.json")

# Inicializa la app
firebase_admin.initialize_app(cred, {
    'storageBucket': 'fightclubcafe.appspot.com'
})

# Clientes
db = firestore.client()       # Firestore
bucket = storage.bucket()     # Storage
