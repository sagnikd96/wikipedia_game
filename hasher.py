"""
Hashes strings
"""

import hashlib

ALGORITHM = "ripemd160"

def gen_hash(string, algorithm=ALGORITHM):
    h = hashlib.new(algorithm)
    h.update(string.encode())
    return h.hexdigest()
