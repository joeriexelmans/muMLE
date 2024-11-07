from zlib import compress
import base64
import string

maketrans = bytes.maketrans

# Includes code fragments from: https://github.com/dougn/python-plantuml/blob/bb5407e87aabbac9e8baef5a6726b03f72afca16/plantuml.py
# Copyright (c) 2013, Doug Napoleone and then Copyright (c) 2015, Samuel Marks

plantuml_alphabet = string.digits + string.ascii_uppercase + string.ascii_lowercase + '-_'
base64_alphabet   = string.ascii_uppercase + string.ascii_lowercase + string.digits + '+/'
b64_to_plantuml = maketrans(base64_alphabet.encode('utf-8'), plantuml_alphabet.encode('utf-8'))

def encode(plantuml_text: str) -> str:
    zlibbed_str = compress(plantuml_text.encode('utf-8'))
    compressed_string = zlibbed_str[2:-4]
    return base64.b64encode(compressed_string).translate(b64_to_plantuml).decode('utf-8')

def make_url(plantuml_text: str) -> str:
    encoded = encode(plantuml_text)
    return f"https://deemz.org/plantuml/pdf/{encoded}"
