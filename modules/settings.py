# Biometric Authentication System Settings

# Face Recognition Thresholds
FACE_THRESHOLD = 0.6  # Cosine similarity threshold (0.0 to 1.0)
# Higher = more strict, Lower = more lenient
# Recommended: 0.5-0.7 for good security/usability balance

# Fingerprint Recognition Thresholds
FINGERPRINT_THRESHOLD = 0.3  # Minutiae match score threshold (0.0 to 1.0)
# Higher = more strict, Lower = more lenient
# Recommended: 0.2-0.4 for fingerprint matching

# Database Configuration
DATABASE_PATH = "database/users.db"

# Liveness Detection Settings
LIVENESS_TEXTURE_THRESHOLD = 100  # Laplacian variance threshold
LIVENESS_DEPTH_THRESHOLD = 0.015  # 3D depth threshold
LIVENESS_OVERALL_THRESHOLD = 0.6  # Overall liveness score threshold

# Security Settings
PASSWORD_HASH_ALGORITHM = "md5"  # NOTE: Use bcrypt or argon2 in production!
SESSION_TIMEOUT = 3600  # seconds (1 hour)

# Image Processing Settings
MAX_IMAGE_SIZE = 5000  # Maximum image dimension in pixels
MIN_IMAGE_SIZE = 50    # Minimum image dimension in pixels
FACE_DETECTION_SCALE = 800  # Resize large images for faster face detection

# Enrollment Settings
MIN_FACE_QUALITY = 0.5  # Minimum quality score for face enrollment
MIN_FINGERPRINT_MINUTIAE = 10  # Minimum minutiae count for fingerprint enrollment