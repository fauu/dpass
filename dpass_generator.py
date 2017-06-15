# pylint: disable=missing-docstring
import hashlib

SECRET = "SECRET"

def generate_example(service_name, pin):
    service_name = service_name.strip() # strip whitespace
    service_name = service_name.replace("http://", "") # strip "http://"
    if service_name[-1] == "/":
        service_name = service_name[:-1] # strip trailing slash

    # password = md5(service_name + SECRET + PIN)
    message = hashlib.md5()
    message.update(service_name.encode("utf-8"))
    message.update(SECRET.encode("utf-8"))
    message.update(pin.encode("utf-8"))
    password = message.hexdigest()

    return password
