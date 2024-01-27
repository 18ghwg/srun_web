# 正常版
import base64


# 加密
def enkey(code: str):
    _key = base64.b64encode(code.encode())
    _key = _key.decode()[:4] + "ghwg" + _key.decode()[4:]
    return _key


# 解密
def dekey(code: str):
    key = str(code[:4] + code[8:])
    res = base64.b64decode(key)
    return res.decode()
