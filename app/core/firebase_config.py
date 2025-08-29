import firebase_admin
from firebase_admin import credentials
import os
import json

def initialize_firebase():
    """
    Initializes the Firebase Admin SDK using a service account key
    from an environment variable.
    """
    if not firebase_admin._apps:
        try:
            # Get the JSON string from the environment variable
            service_account_json_str = os.getenv('FIREBASE_SERVICE_ACCOUNT_JSON')
            if service_account_json_str is None:
                raise ValueError("FIREBASE_SERVICE_ACCOUNT_JSON env var not set.")

            # Convert the JSON string to a dictionary
            service_account_info = json.loads(service_account_json_str)

            # Initialize the app with the credentials
            cred = credentials.Certificate(service_account_info)
            firebase_admin.initialize_app(cred)
            print("Firebase initialized successfully from environment variable.")
        except Exception as e:
            print(f"Failed to initialize Firebase: {e}")