from hashlib import sha256


def get_hash_string(input_string):
    return sha256(input_string.encode()).hexdigest()
