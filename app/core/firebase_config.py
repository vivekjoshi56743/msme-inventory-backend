import firebase_admin
from firebase_admin import credentials
import os
import json


def initialize_firebase():
    """
    Initializes the Firebase Admin SDK. It first tries to use credentials
    from an environment variable (for production) and falls back to a local
    service account file (for development).
    """
    if not firebase_admin._apps:
        try:
            # Check for the environment variable used in production (e.g., on Render)
            service_account_json_str = os.getenv('FIREBASE_SERVICE_ACCOUNT_JSON')
            if service_account_json_str:
                print("Initializing Firebase from environment variable...")
                service_account_info = json.loads(service_account_json_str)
                cred = credentials.Certificate(service_account_info)
            else:
                # Fallback to the local file for development
                print("Initializing Firebase from local serviceAccountKey.json file...")
                cred = credentials.Certificate("serviceAccountKey.json")

            firebase_admin.initialize_app(cred)
            print("Firebase initialized successfully.")
        except Exception as e:
            print(f"Failed to initialize Firebase: {e}")