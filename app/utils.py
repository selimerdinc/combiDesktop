def clean_phone(p):
    if not p: return ""
    return "".join(filter(str.isdigit, str(p)))

def clean_float(val):
    if not val: return 0.0
    try: return float(str(val).replace(".", "").replace(",", "."))
    except: return 0.0
