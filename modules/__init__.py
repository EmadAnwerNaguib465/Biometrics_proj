# Modules package initializer
# This file makes the 'modules' directory a Python package

__version__ = "1.1.0"
__author__ = "Biometric Auth System"

# Import main functions for easier access
from .authentication import authenticate_user, authenticate_user_simple
from .face_recognition import verify_face, save_face_embedding, load_face_embedding
from .fingerprint_recognition import verify_fingerprint, save_fingerprint_template, load_fingerprint_template
from .liveness_detection import check_liveness
from .utils import verify_password
from .settings import FACE_THRESHOLD, FINGERPRINT_THRESHOLD

__all__ = [
    'authenticate_user',
    'authenticate_user_simple',
    'verify_face',
    'verify_fingerprint',
    'check_liveness',
    'verify_password',
    'save_face_embedding',
    'load_face_embedding',
    'save_fingerprint_template',
    'load_fingerprint_template',
    'FACE_THRESHOLD',
    'FINGERPRINT_THRESHOLD'
]