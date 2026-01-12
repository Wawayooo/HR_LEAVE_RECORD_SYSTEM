from django.contrib.auth.hashers import check_password, make_password
from .models import AccessKey

def verify_secret_key(input_key):
    try:
        access_key = AccessKey.objects.latest('created_at')
        return check_password(input_key, access_key.key_hash)
    except AccessKey.DoesNotExist:
        return False
