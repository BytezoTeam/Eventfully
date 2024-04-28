from hashlib import sha256


def get_hash_string(input_string):
    hash_string = sha256(input_string.encode()).hexdigest()
    return hash_string
