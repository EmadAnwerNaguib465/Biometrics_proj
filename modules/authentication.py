from modules.face_recognition import verify_face
from modules.fingerprint_recognition import verify_fingerprint
from modules.utils import verify_password
from modules.settings import FACE_THRESHOLD, FINGERPRINT_THRESHOLD

def authenticate_user(face_img, fingerprint_img, password, user_id="default_user", 
                      require_all=False, require_biometric=True):
    """
    Multi-modal authentication with flexible verification modes
    
    Args:
        face_img: Face image for verification
        fingerprint_img: Fingerprint image for verification
        password: Password string for verification
        user_id: User identifier for database lookup
        require_all: If True, all provided factors must pass
        require_biometric: If True, at least one biometric must pass
    
    Returns:
        dict with authentication result, details, and similarity scores
    """
    result = {
        'authenticated': False,
        'factors_passed': [],
        'factors_failed': [],
        'details': {},
        'scores': {}  # NEW: Store similarity/match scores
    }
    
    # Track which factors were attempted
    factors_attempted = []
    factors_passed = []
    
    # 1. Face Verification
    if face_img is not None:
        factors_attempted.append('face')
        try:
            face_ok, face_similarity = verify_face(face_img, threshold=FACE_THRESHOLD, user_id=user_id)
            
            # Store the similarity score
            result['scores']['face_similarity'] = round(face_similarity, 4)
            
            if face_ok:
                factors_passed.append('face')
                result['factors_passed'].append('face')
                result['details']['face'] = f'verified (similarity: {face_similarity:.4f})'
            else:
                result['factors_failed'].append('face')
                result['details']['face'] = f'failed (similarity: {face_similarity:.4f}, threshold: {FACE_THRESHOLD})'
        except Exception as e:
            result['factors_failed'].append('face')
            result['details']['face'] = f'error: {str(e)}'
            result['scores']['face_similarity'] = 0.0
    
    # 2. Fingerprint Verification
    if fingerprint_img is not None:
        factors_attempted.append('fingerprint')
        try:
            finger_ok, fingerprint_score = verify_fingerprint(fingerprint_img, threshold=FINGERPRINT_THRESHOLD, user_id=user_id)
            
            # Store the match score
            result['scores']['fingerprint_match'] = round(fingerprint_score, 4)
            
            if finger_ok:
                factors_passed.append('fingerprint')
                result['factors_passed'].append('fingerprint')
                result['details']['fingerprint'] = f'verified (match: {fingerprint_score:.4f})'
            else:
                result['factors_failed'].append('fingerprint')
                result['details']['fingerprint'] = f'failed (match: {fingerprint_score:.4f}, threshold: {FINGERPRINT_THRESHOLD})'
        except Exception as e:
            result['factors_failed'].append('fingerprint')
            result['details']['fingerprint'] = f'error: {str(e)}'
            result['scores']['fingerprint_match'] = 0.0
    
    # 3. Password Verification (Fallback)
    if password:
        factors_attempted.append('password')
        try:
            pwd_ok = verify_password(password)
            if pwd_ok:
                factors_passed.append('password')
                result['factors_passed'].append('password')
                result['details']['password'] = 'verified'
            else:
                result['factors_failed'].append('password')
                result['details']['password'] = 'failed'
        except Exception as e:
            result['factors_failed'].append('password')
            result['details']['password'] = f'error: {str(e)}'
    
    # Determine authentication result based on mode
    if require_all:
        # All attempted factors must pass
        result['authenticated'] = (len(factors_passed) == len(factors_attempted) 
                                   and len(factors_attempted) > 0)
        result['mode'] = 'require_all'
    elif require_biometric:
        # At least one biometric (face or fingerprint) must pass
        biometric_passed = ('face' in factors_passed or 'fingerprint' in factors_passed)
        result['authenticated'] = biometric_passed
        result['mode'] = 'require_biometric'
    else:
        # Any single factor passing is sufficient
        result['authenticated'] = len(factors_passed) > 0
        result['mode'] = 'any_factor'
    
    # If no biometric passed but password passed (in biometric mode), still fail
    if require_biometric and result['authenticated'] == False:
        if 'password' in factors_passed and len(factors_passed) == 1:
            result['authenticated'] = False
            result['details']['note'] = 'Password alone insufficient in biometric mode'
    
    # Summary
    result['factors_attempted'] = len(factors_attempted)
    result['factors_passed_count'] = len(factors_passed)
    
    return result

def authenticate_user_simple(face_img, fingerprint_img, password, user_id="default_user"):
    """
    Simplified authentication - returns True/False
    Requires: (face AND fingerprint) OR password
    """
    result = authenticate_user(face_img, fingerprint_img, password, user_id, 
                              require_biometric=False)
    
    # Check if both biometrics passed
    if 'face' in result['factors_passed'] and 'fingerprint' in result['factors_passed']:
        return True
    
    # Or if password passed
    if 'password' in result['factors_passed']:
        return True
    
    return False