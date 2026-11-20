"""WinRM probe: test SSPI with current user creds (no explicit identity).
If RED's logged-in user has WinRM rights on PALE/BLACK, this works."""
import socket, base64, uuid
from ctypes import *
from ctypes.wintypes import FILETIME, DWORD, ULONG, USHORT, LPVOID

class SECBUFDESC(Structure):
    _fields_ = [('cbBuffer', ULONG), ('BufferType', c_int), ('pvBuffer', LPVOID)]

sspi = windll.secur32
sspi.AcquireCredentialsHandleW.restype = DWORD
sspi.AcquireCredentialsHandleW.argtypes = [
    c_wchar_p, c_wchar_p, ULONG, LPVOID, LPVOID, c_void_p, c_void_p,
    POINTER(LPVOID), POINTER(FILETIME)
]
sspi.FreeCredentialsHandle.argtypes = [POINTER(LPVOID)]
sspi.InitializeSecurityContextW.restype = DWORD
sspi.InitializeSecurityContextW.argtypes = [
    LPVOID, LPVOID, c_wchar_p, ULONG, DWORD, DWORD,
    POINTER(SECBUFDESC), ULONG, POINTER(LPVOID), c_void_p,
    POINTER(SECBUFDESC), POINTER(ULONG), c_void_p
]
sspi.FreeContextBuffer.argtypes = [LPVOID]

def try_current_user(host_ip):
    """Try WinRM with current user's credentials (no explicit identity)."""
    target = f'http://{host_ip}:5985'
    
    # Acquire creds for CURRENT USER (pvAuthData=None)
    cred = LPVOID()
    expiry = FILETIME()
    r = sspi.AcquireCredentialsHandleW(
        'Negotiate', None, 2,  # SEC_PKG_CRED_OUTBOUND
        None, None, None, None,  # no identity = current user
        byref(cred), byref(expiry)
    )
    if r != 0:
        return f'AcquireCreds failed: 0x{r:08X}'
    
    try:
        # Step 1: Get Type 1 token
        ctx = LPVOID()
        outbufs = (SECBUFDESC * 1)()
        max_out = ULONG(1)
        r = sspi.InitializeSecurityContextW(
            cred, None, target,
            0x01000000 | 0x02000000,  # SEQ_DETECT | REPLAY_DETECT
            0, 0, None, 0,
            byref(ctx), None, byref(outbufs), byref(max_out), None
        )
        if r not in (0, 0x00090312):
            return f'InitSec step1 failed: 0x{r:08X}'
        
        token1 = bytes(outbufs[0].pvBuffer, outbufs[0].cbBuffer)
        sspi.FreeContextBuffer(outbufs[0].pvBuffer)
        auth1 = 'Negotiate ' + base64.b64encode(token1).decode()
        
        # Send SOAP request
        soap = _make_soap(host_ip)
        resp = _http_post(host_ip, soap, auth1)
        status_line = resp.split('\r\n')[0]
        
        if '200' in status_line:
            return f'AUTH OK (current user) - {status_line}'
        if '401' not in status_line:
            return f'Unexpected: {status_line}'
        
        # Extract challenge
        challenge_b64 = None
        for line in resp.split('\r\n'):
            if line.lower().startswith('www-authenticate:'):
                val = line.split(':', 1)[1].strip()
                if 'Negotiate' in val:
                    challenge_b64 = val.split('Negotiate', 1)[1].strip()
                break
        if not challenge_b64:
            return f'No Negotiate in 401: {resp[:200]}'
        
        # Step 2: Process challenge
        challenge = base64.b64decode(challenge_b64)
        inbuf = SECBUFDESC()
        inbuf.cbBuffer = len(challenge)
        inbuf.BufferType = 19
        inbuf.pvBuffer = cast(create_string_buffer(challenge, len(challenge)), LPVOID)
        
        outbufs2 = (SECBUFDESC * 1)()
        max_out2 = ULONG(1)
        r = sspi.InitializeSecurityContextW(
            cred, ctx, None,
            0x01000000 | 0x02000000,
            0, 0, byref(inbuf), 1,
            byref(ctx), None, byref(outbufs2), byref(max_out2), None
        )
        if r not in (0, 0x00090312):
            return f'InitSec step2 failed: 0x{r:08X}'
        
        token3 = bytes(outbufs2[0].pvBuffer, outbufs2[0].cbBuffer)
        sspi.FreeContextBuffer(outbufs2[0].pvBuffer)
        auth2 = 'Negotiate ' + base64.b64encode(token3).decode()
        
        # Retry
        resp2 = _http_post(host_ip, soap, auth2)
        status2 = resp2.split('\r\n')[0]
        return f'Type3 sent -> {status2}'
    finally:
        sspi.FreeCredentialsHandle(byref(cred))

def _http_post(host_ip, body, auth_header):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(15)
    s.connect((host_ip, 5985))
    req = (
        f'POST /wsman HTTP/1.1\r\nHost: {host_ip}:5985\r\n'
        f'Content-Type: application/soap+xml; charset=utf-8\r\n'
        f'Authorization: {auth_header}\r\n'
        f'Content-Length: {len(body.encode())}\r\nConnection: close\r\n\r\n'
    )
    s.sendall(req.encode() + body.encode())
    data = b''
    while True:
        try:
            c = s.recv(65536)
            if not c: break
            data += c
        except socket.timeout: break
    s.close()
    return data.decode('utf-8', errors='replace')

def _make_soap(host_ip):
    mid = f'uuid:{uuid.uuid4()}'
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<s:Envelope xmlns:s="http://www.w3.org/2003/05/soap-envelope">'
        '<s:Header>'
        f'<wsa:To xmlns:wsa="http://www.w3.org/2005/08/addressing">http://{host_ip}:5985/wsman</wsa:To>'
        '<wsa:Action xmlns:wsa="http://www.w3.org/2005/08/addressing">'
        'http://schemas.dmtf.org/wbem/ws-man/1/Create</wsa:Action>'
        f'<wsa:MessageID xmlns:wsa="http://www.w3.org/2005/08/addressing">{mid}</wsa:MessageID>'
        '</s:Header><s:Body>'
        '<wsmid:CreateRequest xmlns:wsmid="http://schemas.dmtf.org/wbem/ws-man/1/cim-schema/1">'
        '<wsmid:ResourceURI>http://schemas.dmtf.org/wbem/ws-man/1/cim-schema/1/CIM_20_WSMan</wsmid:ResourceURI>'
        '</wsmid:CreateRequest></s:Body></s:Envelope>'
    )

if __name__ == '__main__':
    for name, ip in [('PALE','IP_PALE'), ('BLACK','IP_BLACK')]:
        result = try_current_user(ip)
        print(f'{name} ({ip}): {result}')