"""WinRM NTLM full auth: pure Python NTLM Type 1+3, no external deps.
Tests WinRM Create on PALE + BLACK (reachable from sandbox)."""
import socket, struct, uuid, base64, json

# ===== MD4 =====
def md4(data):
    """Pure Python MD4."""
    def rotl(x, n): return ((x << n) | (x >> (32 - n))) & 0xFFFFFFFF
    def F(x,y,z): return (x & y) | (~x & z) & 0xFFFFFFFF
    def G(x,y,z): return (x & y) | (x & z) | (y & z) & 0xFFFFFFFF
    def H(x,y,z): return x ^ y ^ z
    
    msg = bytearray(data)
    orig_len = len(data)
    msg.append(0x80)
    while len(msg) % 64 != 56:
        msg.append(0)
    msg.extend(struct.pack('<Q', orig_len * 8))
    
    a, b, c, d = 0x67452301, 0xEFCDAB89, 0x98BADCFE, 0x10325476
    s1 = [3,7,11,19]; s2 = [3,5,9,13]; s3 = [3,9,11,15]
    
    for i in range(0, len(msg), 64):
        X = list(struct.unpack('<16I', msg[i:i+64]))
        A,B,C,D = a,b,c,d
        
        # Round 1: a = rotl(a + F(b,c,d) + X[j], s)
        for j in range(16):
            if j < 4: f, k = F(B,C,D), 0
            elif j < 8: f, k = F(B,C,D), 0x5A827999
            elif j < 12: f, k = F(B,C,D), 0x6ED9EBA1
            else: f, k = F(B,C,D), 0xA953FD4E
            idx = [0,1,2,3,5,7,9,11,4,6,8,10,1,3,5,7][j]
            A, B, C, D = D, C, rotl(B + f + X[idx] + k & 0xFFFFFFFF, s1[j%4]), A
        
        # Round 2: a = rotl(a + G(b,c,d) + X[j] + K, s)
        for j in range(16):
            if j < 4: k = 0x5A827999
            elif j < 8: k = 0x6ED9EBA1
            elif j < 12: k = 0x8F1BBCDC
            else: k = 0xA953FD4E
            idx = [0,4,8,12,1,5,9,13,2,6,10,14,3,7,11,15][j]
            A, B, C, D = D, C, rotl(B + G(B,C,D) + X[idx] + k & 0xFFFFFFFF, s2[j%4]), A
        
        # Round 3: a = rotl(a + H(b,c,d) + X[j] + K, s)
        for j in range(16):
            if j < 4: k = 0x5A827999
            elif j < 8: k = 0x6ED9EBA1
            elif j < 12: k = 0x8F1BBCDC
            else: k = 0xA953FD4E
            idx = [0,8,4,12,2,10,6,14,1,9,5,13,3,11,7,15][j]
            A, B, C, D = D, C, rotl(B + H(B,C,D) + X[idx] + k & 0xFFFFFFFF, s3[j%4]), A
        
        a = (a+A) & 0xFFFFFFFF; b = (b+B) & 0xFFFFFFFF
        c = (c+C) & 0xFFFFFFFF; d = (d+D) & 0xFFFFFFFF
    return struct.pack('<IIII', a, b, c, d)

# ===== DES (for NTLM) =====
# DES S-boxes and tables
DES_PC1 = [57,49,41,33,25,17,9,1,58,50,42,34,26,18,10,2,
           59,51,43,35,27,19,11,3,60,52,44,36,63,55,47,39,31,23,15,7,
           62,54,46,38,30,22,14,6,61,53,45,37,29,21,13,5,28,20,12,4]
DES_PC2 = [14,17,11,24,1,5,3,28,15,6,21,10,23,19,12,4,
           26,8,16,7,27,20,13,2,41,52,31,37,47,55,30,40,
           51,45,33,48,44,49,39,56,34,53,46,42,50,36,29,32]
DES_IP = [58,50,42,34,26,18,10,2,60,52,44,36,28,20,12,4,
          62,54,46,38,30,22,14,6,64,56,48,40,32,24,16,8,
          57,49,41,33,25,17,9,1,59,51,43,35,27,19,11,3,
          61,53,45,37,29,21,13,5,63,55,47,39,31,23,15,7]
DES_FP = [40,8,48,16,56,24,64,32,39,7,47,15,55,23,63,31,
          38,6,46,14,54,22,62,30,37,5,45,13,53,21,61,29,
          36,4,44,12,52,20,60,28,35,3,43,11,51,19,59,27,
          34,2,42,10,50,18,58,26,33,1,41,9,49,17,57,25]
S_BOXES = [
    [[14,4,13,1,2,15,11,8,3,10,6,12,5,9,0,7],[0,15,7,4,14,2,13,1,10,6,12,11,9,5,3,8],
     [4,1,14,8,13,6,2,11,15,12,9,7,3,10,5,0],[15,12,8,2,4,9,1,7,5,11,3,14,10,0,6,13]],
    [[15,1,8,14,6,11,3,4,9,7,2,13,12,0,5,10],[3,13,4,7,15,2,8,14,12,0,1,10,6,9,11,5],
     [0,14,7,11,10,4,13,1,5,8,12,6,9,3,2,15],[13,8,10,1,3,15,4,2,11,6,7,12,0,5,14,9]],
    [[10,0,9,14,6,3,15,5,1,13,12,7,11,4,2,8],[13,7,0,9,3,4,6,10,2,8,5,14,12,11,15,1],
     [13,6,4,9,8,15,3,0,11,1,2,12,5,10,14,7],[7,13,13,8,15,6,3,12,10,1,0,4,2,11,5,9]],
    [[15,12,8,2,4,9,1,7,5,11,3,14,10,0,6,13],[15,4,8,2,13,6,2,11,10,12,9,7,5,14,3,1],
     [2,13,4,15,11,8,12,3,7,0,1,10,14,6,9,5],[12,1,10,15,9,2,6,8,0,13,3,4,14,7,5,11]],
    [[13,8,10,1,3,15,4,2,11,6,7,12,0,5,14,9],[10,1,13,14,7,6,12,11,2,8,9,5,0,15,4,3],
     [6,12,13,1,3,8,9,4,5,11,10,0,7,2,15,14],[13,4,11,2,15,8,1,10,12,6,3,9,5,7,0,14]],
    [[13,1,15,12,5,10,0,8,4,2,14,3,9,7,6,11],[4,11,10,13,7,8,1,6,15,5,3,2,12,9,0,14],
     [10,15,12,2,7,8,4,1,14,6,9,11,3,0,5,13],[11,8,12,7,1,14,2,13,6,15,0,9,10,4,5,3]],
    [[15,12,8,2,4,9,1,7,5,11,3,14,10,0,6,13],[15,1,8,14,6,11,3,4,9,7,2,13,12,0,5,10],
     [4,1,14,8,13,6,2,11,15,12,9,7,3,10,5,0],[15,12,8,2,4,9,1,7,5,11,3,14,10,0,6,13]],
    [[15,1,8,14,6,11,3,4,9,7,2,13,12,0,5,10],[3,13,4,7,15,2,8,14,12,0,1,10,6,9,11,5],
     [0,14,7,11,10,4,13,1,5,8,12,6,9,3,2,15],[13,8,10,1,3,15,4,2,11,6,7,12,0,5,14,9]],
]
EXPANSION = [32,1,2,3,4,5,4,5,6,7,8,9,8,9,10,11,12,13,
             12,13,14,15,16,17,16,17,18,19,20,21,20,21,22,23,24,25,
             24,25,26,27,28,29,28,29,30,31,32,1]
SHIFTS = [1,1,2,2,2,2,2,2,1,2,2,2,2,2,2,1]

def des_permute(data, perm):
    return bytes((data[(p-1)//8] >> (7-(p-1)%8)) & 1 for p in perm)

def des_key_schedule(key_64bit):
    """Generate 16 subkeys from 64-bit key."""
    # PC1: 64 -> 56 bits
    k = des_permute(key_64bit, DES_PC1)
    c, d = k[:7], k[7:]
    
    def rotate_left(data, n):
        return data[n:] + data[:n]
    
    subkeys = []
    for i in range(16):
        c = rotate_left(c, SHIFTS[i])
        d = rotate_left(d, SHIFTS[i])
        cd = c + d
        subkey = des_permute(cd, DES_PC2)
        subkeys.append(subkey)
    return subkeys

def des_encrypt_block(block_8bytes, subkeys):
    """Encrypt one 8-byte block with DES."""
    # Initial permutation
    data = des_permute(block_8bytes, DES_IP)
    left, right = data[:4], data[4:]
    
    for i in range(16):
        # Expansion: 32 -> 48 bits
        expanded = bytes((right[(p-1)//8] >> (7-(p-1)%8)) & 1 for p in EXPANSION)
        # XOR with subkey
        xored = bytes(a ^ b for a, b in zip(expanded, subkeys[i]))
        
        # S-boxes: 48 -> 32 bits
        sbox_out = []
        for j in range(8):
            chunk = xored[j*6:(j+1)*6]
            row = (chunk[0] << 1) | chunk[5]
            col = (chunk[1] << 3) | (chunk[2] << 2) | (chunk[3] << 1) | chunk[4]
            val = S_BOXES[j][row][col]
            sbox_out.extend([(val >> (3-k)) & 1 for k in range(4)])
        # Pack bits to bytes
        sbox_result = bytearray(4)
        for bit_i, bit in enumerate(sbox_out):
            sbox_result[bit_i // 8] |= bit << (7 - bit_i % 8)
        
        # XOR with left, swap
        new_right = bytes(a ^ b for a, b in zip(left, bytes(sbox_result)))
        left, right = right, new_right
    
    # Final: right + left (no swap), then FP
    combined = right + left
    return des_permute(combined, DES_FP)

def ntlm_nt_response(password, server_challenge):
    """Compute NTLM response to challenge."""
    # NTOWFv1 = MD4(UTF-16LE(password))
    ntowf = md4(password.encode('utf-16-le'))
    
    # Pad to 21 bytes
    padded = ntowf + b'\x00' * 5
    
    # DES encrypt challenge with each 7-byte key
    result = b''
    for i in range(3):
        key_7 = padded[i*7:(i+1)*7]
        # Expand to 8 bytes for DES (add parity bits)
        key_64 = bytearray(8)
        for j in range(7):
            # Each 7-bit group becomes a byte with odd parity
            val = key_7[j]
            key_64[j] = ((val << 1) | (1 - bin(val).count('1') % 2)) & 0xFF
        subkeys = des_key_schedule(bytes(key_64))
        result += des_encrypt_block(server_challenge, subkeys)
    return result

def ntlm_type1():
    flags = 0x00078207
    msg = b'NTLMSSP\x00' + struct.pack('<I', 1) + struct.pack('<I', flags)
    msg += struct.pack('<HHII', 0, 0, 0, 0)
    msg += struct.pack('<HHII', 0, 0, 0, 0)
    return msg

def ntlm_type3(type2, user, domain, password):
    """Build NTLM Type 3 (Authenticate) message."""
    server_challenge = type2[24:32]
    flags = struct.unpack('<I', type2[20:24])[0] & 0x00078207
    
    nt_resp = ntlm_nt_response(password, server_challenge)
    lm_resp = b'\x00' * 24  # LM disabled
    
    user_b = user.encode('utf-16-le')
    domain_b = (domain or '').encode('utf-16-le')
    
    msg = b'NTLMSSP\x00' + struct.pack('<I', 3)
    off = 64
    msg += struct.pack('<HHII', len(lm_resp), len(lm_resp), off, 1); off += len(lm_resp)
    msg += struct.pack('<HHII', len(nt_resp), len(nt_resp), off, 1); off += len(nt_resp)
    msg += struct.pack('<HHII', len(domain_b), len(domain_b), off, 1); off += len(domain_b)
    msg += struct.pack('<HHII', len(user_b), len(user_b), off, 1); off += len(user_b)
    msg += struct.pack('<HHII', 0, 0, 0, 0)  # Workstation
    msg += struct.pack('<HHII', 0, 0, 0, 0)  # Session key
    msg += struct.pack('<I', flags)
    msg += b'\x00' * 8  # Version
    
    msg += lm_resp + nt_resp + domain_b + user_b
    return msg

def http_post(ip, path, headers, body=b''):
    s = socket.socket(); s.settimeout(15); s.connect((ip, 5985))
    hdrs = 'POST %s HTTP/1.1\r\nHost: %s:5985\r\n' % (path, ip)
    for k, v in headers.items():
        hdrs += '%s: %s\r\n' % (k, v)
    hdrs += 'Content-Length: %d\r\nConnection: close\r\n\r\n' % len(body)
    s.sendall(hdrs.encode() + body)
    rd = b''
    while True:
        try: c = s.recv(8192)
        except socket.timeout: break
        if not c: break
        rd += c
    s.close()
    return rd.decode('utf-8', 'replace')

def get_challenge(resp):
    for ln in resp.split('\r\n'):
        if ln.lower().startswith('www-authenticate:'):
            val = ln.split(':', 1)[1].strip()
            if val.startswith('Negotiate '): return val[10:]
            return val
    return None

SOAP_CREATE = ('<?xml version="1.0" encoding="UTF-8"?>'
    '<s:Envelope xmlns:s="http://www.w3.org/2003/05/soap-envelope"><s:Header>'
    '<wsa:To xmlns:wsa="http://www.w3.org/2005/08/addressing">%s/wsman</wsa:To>'
    '<wsa:Action xmlns:wsa="http://www.w3.org/2005/08/addressing">'
    'http://schemas.dmtf.org/wbem/ws-man/1/Create</wsa:Action>'
    '<wsa:MessageID xmlns:wsa="http://www.w3.org/2005/08/addressing">uuid:%s</wsa:MessageID>'
    '</s:Header><s:Body>'
    '<wsmid:CreateRequest xmlns:wsmid="http://schemas.dmtf.org/wbem/ws-man/1/cim-schema/1">'
    '<wsmid:ResourceURI>http://schemas.dmtf.org/wbem/ws-man/1/cim-schema/1/CIM_20_WSMan</wsmid:ResourceURI>'
    '</wsmid:CreateRequest></s:Body></s:Envelope>')

def test_host(ip, user, pw):
    target = 'http://%s:5985' % ip
    msgid = str(uuid.uuid4())
    soap = SOAP_CREATE % (target, msgid)
    
    # Step 1: Type 1
    t1 = ntlm_type1()
    resp = http_post(ip, '/wsman', {
        'Content-Type': 'application/soap+xml; charset=utf-8',
        'Authorization': 'Negotiate ' + base64.b64encode(t1).decode()
    }, soap.encode())
    
    sl = resp.split('\r\n')[0]
    if '401' not in sl:
        ok = 'CreateResponse' in resp or '200' in sl
        return '%s | ok=%s | size=%d' % (sl, ok, len(resp))
    
    # Step 2: Parse challenge, generate Type 3
    cb64 = get_challenge(resp)
    if not cb64:
        return '401 no challenge'
    t2 = base64.b64decode(cb64)
    if t2[:8] != b'NTLMSSP\x00':
        return 'Not NTLM: %s' % t2[:16].hex()
    
    t3 = ntlm_type3(t2, user, '', pw)
    
    # Step 3: Send Type 3
    resp2 = http_post(ip, '/wsman', {
        'Content-Type': 'application/soap+xml; charset=utf-8',
        'Authorization': 'Negotiate ' + base64.b64encode(t3).decode()
    }, soap.encode())
    
    sl2 = resp2.split('\r\n')[0]
    ok = 'CreateResponse' in resp2 or 'cim-schema' in resp2 or '200' in sl2
    return '%s | ok=%s | size=%d' % (sl2, ok, len(resp2))

# --- Standalone probe with hostname-as-domain fix ---
import socket, base64, uuid
from datetime import datetime, timezone

def tcp_check(ip, port=5985, timeout=5):
    try:
        s = socket.socket(); s.settimeout(timeout); s.connect((ip, port)); s.close()
        return True
    except Exception as e:
        return f'FAIL: {type(e).__name__}'

def winrm_auth(ip, user, domain, pw):
    """Full NTLM handshake with hostname as domain."""
    msgid = str(uuid.uuid4())
    target = 'http://%s:5985' % ip
    soap = ('<?xml version="1.0" encoding="utf-8"?>'
            '<s:Envelope xmlns:s="http://www.w3.org/2003/05/soap-envelope" '
            'xmlns:wsm="http://docs.oasis-open.org/wsn/2004/08/eventing">'
            '<s:Body><wsm:Create><wsm:ListenerPort>'
            + target + '</wsm:ListenerPort></wsm:Create></s:Body></s:Envelope>')
    headers = {
        'Content-Type': 'application/soap+xml; charset=utf-8',
        'Authorization': 'Negotiate ' + base64.b64encode(ntlm_type1()).decode()
    }
    resp = http_post(ip, '/wsman', headers, soap.encode())
    sl = resp.split('\r\n')[0]
    if '401' not in sl:
        return f'{sl} | no_challenge'
    cb64 = get_challenge(resp)
    if not cb64:
        return '401 no challenge parsed'
    t2 = base64.b64decode(cb64)
    if t2[:8] != b'NTLMSSP\x00':
        return f'Not NTLM: {t2[:16].hex()}'
    # Use hostname (uppercase) as domain for local workgroup accounts
    t3 = ntlm_type3(t2, user, domain, pw)
    headers['Authorization'] = 'Negotiate ' + base64.b64encode(t3).decode()
    resp2 = http_post(ip, '/wsman', headers, soap.encode())
    sl2 = resp2.split('\r\n')[0]
    ok = 'CreateResponse' in resp2 or 'cim-schema' in resp2 or '200' in sl2
    return f'{sl2} | auth_ok={ok}'

results = {'ts': datetime.now(timezone.utc).isoformat(), 'hosts': {}}
for name, ip, user in [('PALE','IP_PALE','pale'), ('BLACK','IP_BLACK','black'), ('RED','[LAN-IP]','red')]:
    tcp = tcp_check(ip)
    results['hosts'][name] = {'tcp_5985': tcp}
    if tcp is True:
        try:
            results['hosts'][name]['ntlm'] = winrm_auth(ip, user, name.upper(), '')
        except Exception as e:
            results['hosts'][name]['ntlm'] = f'ERR: {type(e).__name__}: {e}'

with open('memory/mechanic/winrm-legs.jsonl', 'a') as f:
    f.write(json.dumps(results) + '\n')
print(json.dumps(results, indent=2))
