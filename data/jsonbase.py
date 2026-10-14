import json




def fetchvalue(key, file: str, raise_keyerror: bool = False):
    """Fetch a key's value. 
    ## Returns & Raises
    - None is key doesn't exist.
    - If raise_keyerror is True, KeyError will be raised if key doesn't exist
    """
    with open(f'{file}', 'r') as f:
        data: dict = json.load(f)
    try: return data[key]
    except KeyError: 
        if raise_keyerror: raise KeyError(f"Key {key} doesn't exist.")
        else: return None


def popjson(key, file: str) -> dict:
    """Pop a key in a JSON file. Returns the new dict."""
    try:
        with open(f'{file}', 'r') as f:
            data: dict = json.load(f)
        data.pop(key)
    except KeyError: pass
    return writejson(data, file)

def appendjson(key, value, file: str) -> dict:
    """Edit/Insert a key into a JSON file. Returns the new dict."""
    with open(f'{file}', 'r') as f:
        data: dict = json.load(f)
    if str(key) in data:
        data.pop(str(key))
    data[key] = value
    return writejson(data, file)


def readjson(file: str, convert_to_int: bool = False) -> dict:
    "Read JSON File"
    with open(f'{file}', 'r') as f:
        data = json.load(f)
    if convert_to_int is True:
        d = {}
        for key, value in data.items():
            try: 
                key = int(key)
                d[key] = value
            except ValueError:
                d[key] = value # cant convert to int, append it as it is
                continue
        data = d
    return data

def writejson(data: dict, file: str, *, indent: int = None) -> dict:
    "Write into JSON file"
    with open(f'{file}', 'w') as f:
        json.dump(data, f, indent=indent)
    with open(f'{file}', 'r') as f:
        return json.load(f)

