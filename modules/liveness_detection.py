import cv2
import numpy as np
import mediapipe as mp

# Initialize MediaPipe Face Mesh
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(
    max_num_faces=1,
    refine_landmarks=True,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

# Eye landmarks indices for MediaPipe Face Mesh
LEFT_EYE_INDICES = [33, 160, 158, 133, 153, 144]
RIGHT_EYE_INDICES = [362, 385, 387, 263, 373, 380]

def calculate_ear(eye_landmarks):
    """Calculate Eye Aspect Ratio (EAR)"""
    # Vertical distances
    v1 = np.linalg.norm(eye_landmarks[1] - eye_landmarks[5])
    v2 = np.linalg.norm(eye_landmarks[2] - eye_landmarks[4])
    
    # Horizontal distance
    h = np.linalg.norm(eye_landmarks[0] - eye_landmarks[3])
    
    # Eye Aspect Ratio
    ear = (v1 + v2) / (2.0 * h)
    return ear

def detect_blink(image, ear_threshold=0.2):
    """Detect if eyes are closed (potential blink)"""
    # Convert to RGB for MediaPipe
    if len(image.shape) == 2:
        image_rgb = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
    elif image.shape[2] == 4:
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGRA2RGB)
    else:
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    
    # Process image
    results = face_mesh.process(image_rgb)
    
    if not results.multi_face_landmarks:
        return None, "No face detected"
    
    face_landmarks = results.multi_face_landmarks[0]
    h, w = image.shape[:2]
    
    # Extract eye landmarks
    left_eye = []
    for idx in LEFT_EYE_INDICES:
        landmark = face_landmarks.landmark[idx]
        left_eye.append([landmark.x * w, landmark.y * h])
    left_eye = np.array(left_eye)
    
    right_eye = []
    for idx in RIGHT_EYE_INDICES:
        landmark = face_landmarks.landmark[idx]
        right_eye.append([landmark.x * w, landmark.y * h])
    right_eye = np.array(right_eye)
    
    # Calculate EAR for both eyes
    left_ear = calculate_ear(left_eye)
    right_ear = calculate_ear(right_eye)
    avg_ear = (left_ear + right_ear) / 2.0
    
    is_closed = avg_ear < ear_threshold
    
    return is_closed, avg_ear

def detect_texture(image):
    """Detect texture patterns to distinguish real face from photo"""
    # Convert to grayscale
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image.copy()
    
    # Calculate Laplacian variance (measure of image sharpness/blur)
    laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
    
    # Real faces typically have more texture variation
    # Photos of faces tend to be flatter/blurrier
    return laplacian_var

def detect_face_depth(image):
    """Estimate depth using face size and position"""
    # Convert to RGB for MediaPipe
    if len(image.shape) == 2:
        image_rgb = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
    elif image.shape[2] == 4:
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGRA2RGB)
    else:
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    
    results = face_mesh.process(image_rgb)
    
    if not results.multi_face_landmarks:
        return 0.0
    
    face_landmarks = results.multi_face_landmarks[0]
    h, w = image.shape[:2]
    
    # Get nose tip (landmark 1) and forehead (landmark 10)
    nose = face_landmarks.landmark[1]
    forehead = face_landmarks.landmark[10]
    
    # Calculate z-depth difference (rough 3D estimate)
    depth_diff = abs(nose.z - forehead.z)
    
    return depth_diff

def check_liveness(image, enable_blink=True, enable_texture=True, enable_depth=True):
    """
    Multi-factor liveness detection
    Checks for: blink detection, texture analysis, and depth estimation
    """
    # Convert Streamlit UploadedFile to numpy array
    if hasattr(image, 'read'):
        from PIL import Image
        pil_image = Image.open(image)
        image = np.array(pil_image)
        if len(image.shape) == 3 and image.shape[2] == 3:
            image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
    
    if isinstance(image, bytes):
        nparr = np.frombuffer(image, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    liveness_score = 0
    max_score = 0
    details = {}
    
    # 1. Blink Detection (optional - works better with video)
    if enable_blink:
        max_score += 1
        is_closed, ear_value = detect_blink(image)
        if is_closed is not None:
            details['blink'] = {
                'detected': True,
                'ear': float(ear_value) if isinstance(ear_value, (int, float)) else 0.0,
                'eyes_open': not is_closed
            }
            # For single image, we just check if eyes are detected and open
            if not is_closed:
                liveness_score += 0.5  # Partial score for open eyes
        else:
            details['blink'] = {'detected': False, 'error': ear_value}
    
    # 2. Texture Analysis
    if enable_texture:
        max_score += 1
        texture_score = detect_texture(image)
        details['texture'] = {'score': float(texture_score)}
        
        # Real faces typically have Laplacian variance > 100
        # Photos tend to be < 50
        if texture_score > 100:
            liveness_score += 1
        elif texture_score > 50:
            liveness_score += 0.5
    
    # 3. Depth Estimation
    if enable_depth:
        max_score += 1
        depth_score = detect_face_depth(image)
        details['depth'] = {'score': float(depth_score)}
        
        # Real 3D faces have depth variation > 0.01
        # Flat photos have depth ≈ 0
        if depth_score > 0.015:
            liveness_score += 1
        elif depth_score > 0.008:
            liveness_score += 0.5
    
    # Calculate final liveness probability
    if max_score > 0:
        liveness_probability = liveness_score / max_score
    else:
        liveness_probability = 0.0
    
    details['overall_score'] = float(liveness_probability)
    details['is_live'] = liveness_probability >= 0.6
    
    print(f"Liveness detection: {liveness_probability:.2f} - {'LIVE' if details['is_live'] else 'SPOOFED'}")
    print(f"Details: {details}")
    
    return details['is_live']