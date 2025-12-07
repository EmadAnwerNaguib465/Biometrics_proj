import hashlib
def verify_password(input_pwd, stored_hash="5f4dcc3b5aa765d61d8327deb882cf99"): # default: "password"
    return hashlib.md5(input_pwd.encode()).hexdigest() == stored_hash
