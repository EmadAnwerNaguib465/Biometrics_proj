import cv2
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import pickle
import os

# Initialize OpenCV face detector (no download needed!)
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

def extract_face_embedding(image):
    """Extract face features using OpenCV + histogram"""
    # Convert to grayscale
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image.copy()
    
    # Detect faces
    faces = face_cascade.detectMultiScale(
        gray,
        scaleFactor=1.1,
        minNeighbors=5,
        minSize=(30, 30)
    )
    
    print(f"Detected {len(faces)} face(s)")
    
    if len(faces) == 0:
        print("❌ No face detected. Tips:")
        print("  - Ensure good lighting")
        print("  - Face the camera directly")
        print("  - Remove obstructions (glasses, mask)")
        return None
    
    # Get the largest face
    largest_face = max(faces, key=lambda rect: rect[2] * rect[3])
    x, y, w, h = largest_face
    
    # Extract face region
    face_roi = gray[y:y+h, x:x+w]
    
    # Resize to standard size
    face_resized = cv2.resize(face_roi, (100, 100))
    
    # Normalize
    face_normalized = cv2.equalizeHist(face_resized)
    
    # Create feature vector using multiple methods
    features = []
    
    # 1. HOG features (Histogram of Oriented Gradients)
    hog = cv2.HOGDescriptor((100, 100), (20, 20), (10, 10), (10, 10), 9)
    hog_features = hog.compute(face_normalized)
    features.extend(hog_features.flatten())
    
    # 2. LBP-like features (Local Binary Patterns approximation)
    # Divide face into regions and compute histograms
    regions = 8
    region_h = face_normalized.shape[0] // regions
    region_w = face_normalized.shape[1] // regions
    
    for i in range(regions):
        for j in range(regions):
            region = face_normalized[i*region_h:(i+1)*region_h, j*region_w:(j+1)*region_w]
            hist = cv2.calcHist([region], [0], None, [16], [0, 256])
            features.extend(hist.flatten())
    
    # Convert to numpy array and normalize
    features = np.array(features)
    features = features / (np.linalg.norm(features) + 1e-7)
    
    return features

def save_face_embedding(embedding, user_id="default_user"):
    """Save face features to database"""
    os.makedirs("database", exist_ok=True)
    filepath = f"database/face_{user_id}.pkl"
    with open(filepath, 'wb') as f:
        pickle.dump(embedding, f)
    print(f"✅ Face features saved for user: {user_id}")

def load_face_embedding(user_id="default_user"):
    """Load face features from database"""
    filepath = f"database/face_{user_id}.pkl"
    if not os.path.exists(filepath):
        return None
    with open(filepath, 'rb') as f:
        return pickle.load(f)

def verify_face(image, threshold=0.85, user_id="default_user"):
    """
    Verify face against stored features
    Returns tuple: (passed: bool, similarity_score: float)
    """
    # Load stored features
    stored_features = load_face_embedding(user_id)
    if stored_features is None:
        print("⚠️ No face template found. Please enroll first.")
        return False, 0.0
    
    # Convert Streamlit UploadedFile to numpy array
    if hasattr(image, 'read'):
        from PIL import Image as PILImage
        pil_image = PILImage.open(image)
        image = np.array(pil_image)
        if len(image.shape) == 3 and image.shape[2] == 3:
            image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
    
    # Convert image if needed (from bytes)
    if isinstance(image, bytes):
        nparr = np.frombuffer(image, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    # Extract features from input image
    current_features = extract_face_embedding(image)
    if current_features is None:
        print("❌ No face detected in image")
        return False, 0.0
    
    # Calculate similarity
    similarity = cosine_similarity(
        current_features.reshape(1, -1),
        stored_features.reshape(1, -1)
    )[0][0]
    
    passed = similarity >= threshold
    
    print(f"Face similarity: {similarity:.3f} (threshold: {threshold}) - {'PASS' if passed else 'FAIL'}")
    
    return passed, float(similarity)