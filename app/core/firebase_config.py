import firebase_admin
from firebase_admin import credentials

def initialize_firebase():
    """
    Initializes the Firebase Admin SDK if not already initialized.
    """
    if not firebase_admin._apps:
        try:
            cred = credentials.Certificate("serviceAccountKey.json")
            firebase_admin.initialize_app(cred)
            print("Firebase initialized successfully.")
        except Exception as e:
            print(f"Failed to initialize Firebase: {e}")