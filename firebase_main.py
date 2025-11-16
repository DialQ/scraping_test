from firebase_functions import https_fn
from firebase_admin import initialize_app
from main import app

initialize_app()


@https_fn.on_request()
def api(req: https_fn.Request) -> https_fn.Response:
    """Firebase Cloud Function entry point for FastAPI app"""
    from mangum import Mangum
    
    handler = Mangum(app, lifespan="off")
    return handler(req, None)
