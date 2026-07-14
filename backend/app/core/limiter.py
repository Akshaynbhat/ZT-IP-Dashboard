from slowapi import Limiter
from slowapi.util import get_remote_address

# Setup global limiter resolving limits by client IP address
limiter = Limiter(key_func=get_remote_address)
