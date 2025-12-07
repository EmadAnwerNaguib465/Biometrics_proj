import cv2
import numpy as np
import pickle
import os

def enhance_fingerprint(image):
    """Enhance fingerprint image using various techniques"""
    # Convert to grayscale if needed
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image.copy()
    
    # Normalize
    normalized = cv2.normalize(gray, None, 0, 255, cv2.NORM_MINMAX)
    
    # Apply Gaussian blur to reduce noise
    blurred = cv2.GaussianBlur(normalized, (5, 5), 0)
    
    # Apply adaptive thresholding
    enhanced = cv2.adaptiveThreshold(
        blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY, 11, 2
    )
    
    # Apply morphological operations to clean up
    kernel = np.ones((3, 3), np.uint8)
    enhanced = cv2.morphologyEx(enhanced, cv2.MORPH_CLOSE, kernel)
    enhanced = cv2.morphologyEx(enhanced, cv2.MORPH_OPEN, kernel)
    
    return enhanced

def extract_minutiae(image):
    """Extract fingerprint minutiae (ridge endings and bifurcations)"""
    enhanced = enhance_fingerprint(image)
    
    # Apply thinning using morphological skeleton
    size = np.size(enhanced)
    skel = np.zeros(enhanced.shape, np.uint8)
    element = cv2.getStructuringElement(cv2.MORPH_CROSS, (3, 3))
    
    done = False
    temp = enhanced.copy()
    while not done:
        eroded = cv2.erode(temp, element)
        opened = cv2.morphologyEx(eroded, cv2.MORPH_OPEN, element)
        subset = eroded - opened
        skel = cv2.bitwise_or(skel, subset)
        temp = eroded.copy()
        
        zeros = size - cv2.countNonZero(temp)
        if zeros == size:
            done = True
    
    # Detect minutiae using crossing number method
    minutiae = []
    h, w = skel.shape
    
    for i in range(1, h - 1):
        for j in range(1, w - 1):
            if skel[i, j] == 255:  # Ridge pixel
                # Calculate crossing number
                cn = 0
                neighbors = [
                    skel[i-1, j], skel[i-1, j+1], skel[i, j+1], skel[i+1, j+1],
                    skel[i+1, j], skel[i+1, j-1], skel[i, j-1], skel[i-1, j-1]
                ]
                
                for k in range(8):
                    cn += abs(int(neighbors[k] // 255) - int(neighbors[(k+1) % 8] // 255))
                
                cn = cn // 2
                
                # Ridge ending (cn = 1) or bifurcation (cn = 3)
                if cn == 1 or cn == 3:
                    minutiae.append({
                        'position': (j, i),
                        'type': 'ending' if cn == 1 else 'bifurcation',
                        'orientation': calculate_orientation(skel, i, j)
                    })
    
    return minutiae

def calculate_orientation(image, i, j, window_size=5):
    """Calculate ridge orientation at a point"""
    h, w = image.shape
    half_w = window_size // 2
    
    i_min = max(0, i - half_w)
    i_max = min(h, i + half_w + 1)
    j_min = max(0, j - half_w)
    j_max = min(w, j + half_w + 1)
    
    window = image[i_min:i_max, j_min:j_max]
    
    # Calculate gradient
    gx = cv2.Sobel(window, cv2.CV_64F, 1, 0, ksize=3)
    gy = cv2.Sobel(window, cv2.CV_64F, 0, 1, ksize=3)
    
    # Calculate orientation
    orientation = np.arctan2(gy.sum(), gx.sum())
    return orientation

def match_minutiae(minutiae1, minutiae2, threshold=0.7):
    """Match two sets of minutiae using spatial and orientation similarity"""
    if len(minutiae1) == 0 or len(minutiae2) == 0:
        return 0.0
    
    matches = 0
    tolerance_distance = 20  # pixels
    tolerance_angle = np.pi / 6  # 30 degrees
    
    for m1 in minutiae1:
        for m2 in minutiae2:
            # Check type match
            if m1['type'] != m2['type']:
                continue
            
            # Check spatial distance
            dist = np.sqrt(
                (m1['position'][0] - m2['position'][0]) ** 2 +
                (m1['position'][1] - m2['position'][1]) ** 2
            )
            
            if dist > tolerance_distance:
                continue
            
            # Check orientation
            angle_diff = abs(m1['orientation'] - m2['orientation'])
            angle_diff = min(angle_diff, 2 * np.pi - angle_diff)
            
            if angle_diff < tolerance_angle:
                matches += 1
                break
    
    # Calculate match score
    score = matches / max(len(minutiae1), len(minutiae2))
    return score

def save_fingerprint_template(image, user_id="default_user"):
    """Extract and save fingerprint minutiae"""
    minutiae = extract_minutiae(image)
    
    os.makedirs("database", exist_ok=True)
    filepath = f"database/fingerprint_{user_id}.pkl"
    
    with open(filepath, 'wb') as f:
        pickle.dump(minutiae, f)
    
    print(f"✅ Fingerprint template saved for user: {user_id} ({len(minutiae)} minutiae)")

def load_fingerprint_template(user_id="default_user"):
    """Load fingerprint minutiae from database"""
    filepath = f"database/fingerprint_{user_id}.pkl"
    if not os.path.exists(filepath):
        return None
    
    with open(filepath, 'rb') as f:
        return pickle.load(f)

def verify_fingerprint(image, threshold=0.3, user_id="default_user"):
    """
    Verify fingerprint against stored template
    Returns tuple: (passed: bool, match_score: float)
    """
    # Load stored template
    stored_minutiae = load_fingerprint_template(user_id)
    if stored_minutiae is None:
        print("⚠️ No fingerprint template found. Please enroll first.")
        return False, 0.0
    
    # Convert Streamlit UploadedFile to numpy array
    if hasattr(image, 'read'):
        from PIL import Image
        pil_image = Image.open(image)
        image = np.array(pil_image)
        # Convert to grayscale if needed
        if len(image.shape) == 3:
            image = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    
    # Convert input image from bytes if needed
    if isinstance(image, bytes):
        nparr = np.frombuffer(image, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_GRAYSCALE)
    
    # Extract minutiae from input
    current_minutiae = extract_minutiae(image)
    if len(current_minutiae) == 0:
        print("❌ No minutiae detected in fingerprint")
        return False, 0.0
    
    # Match minutiae
    score = match_minutiae(stored_minutiae, current_minutiae)
    passed = score >= threshold
    
    print(f"Fingerprint match score: {score:.3f} (threshold: {threshold}) - {'PASS' if passed else 'FAIL'}")
    
    return passed, float(score)