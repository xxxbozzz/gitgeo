import re

with open('/Users/kev/Library/Application Support/Antigravity/User/globalStorage/highagency.pencildev/editor/assets/pencil.wasm', 'rb') as f:
    data = f.read()
    strings = re.findall(b'[ -~]{5,}', data)
    for s in strings:
        if b'Unsupported' in s or b'version' in s or b'format' in s:
            try:
                line = s.decode('ascii')
                if 'format' in line.lower() or 'version' in line.lower():
                    # print(line)
                    pass
            except:
                pass
            
    # Try just finding the exact error pattern
    for s in strings:
        try:
            line = s.decode('ascii')
            if 'Unsupported' in line:
                print(line)
        except:
            pass
