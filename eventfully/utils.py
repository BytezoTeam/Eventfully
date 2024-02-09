import hashlib
import random
import string
import eventfully.database as db


# Thank you, ChatGPT!
def get_hash_string(input_string):
    # Create a new SHA-256 hash object
    hash_object = hashlib.sha1()

    # Convert the input string to bytes
    input_bytes = input_string.encode('utf-8')

    # Update the hash object with the input bytes
    hash_object.update(input_bytes)

    # Get the hexadecimal representation of the hash
    hash_string = hash_object.hexdigest()

    return hash_string


def createUserId(length=4):
    # Generate 4 groups of 4 characters or digits separated by '-'
    groups = [
        ''.join(random.choices(string.ascii_lowercase + string.digits, k=4))
        for _ in range(length)
    ]

    # Combine the groups with '-'
    userId = '-'.join(groups)

    if db.AccountData.select().where(db.AccountData.userID == userId).exists():
        createUserId(length)

    return userId
