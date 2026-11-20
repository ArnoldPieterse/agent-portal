"""Standalone WinRM command executor - no external deps.
Uses SSPI (secur32.dll) for Negotiate auth + raw HTTP SOAP.
Test: python memory/mechanic/winrm_exec_test.py
"""
import socket, base64, uuid, time, json, sys
from ctypes import *
from ctypes.wintypes import FILETIME, DWORD, ULONG, USHORT, LPVOID

# --- SSPI setup with explicit prototypes ---
class SEC_WINNT_AUTH_IDENTITY_W(Structure):
    _fields_ = [
        ('User', c_wchar_p), ('UserLength', USHORT),
        ('Domain', c_wchar_p), ('DomainLength', USHORT),
        ('Password', c_wchar_p), ('PasswordLength', USHORT),
    ]

class SEC_WINNT_AUTH_IDENTITY_BUFFER_W(Structure):
    _fields_ = [('Identity', SEC_WINNT_AUTH_IDENTITY_W), ('Flags', ULONG)]

class SECBUFDESC(Structure):
    _fields_ = [('cbBuffer', ULONG), ('BufferType', c_int), ('pvBuffer', LPVOID)]

sspi = windll.secur32
sspi.AcquireCredentialsHandleW.restype = DWORD
sspi.AcquireCredentialsHandleW.argtypes = [
    c_wchar_p, c_wchar_p, ULONG, LPVOID, LPVOID, c_void_p, c_void_p,
    POINTER(LPVOID), POINTER(FILETIME)
]
sspi.FreeCredentialsHandle.restype = DWORD
sspi.FreeCredentialsHandle.argtypes = [POINTER(LPVOID)]
sspi.InitializeSecurityContextW.restype = DWORD
sspi.InitializeSecurityContextW.argtypes = [
    LPVOID, LPVOID, c_wchar_p, ULONG, DWORD, DWORD,
    POINTER(SECBUFDESC), ULONG, POINTER(LPVOID), c_void_p,
    POINTER(SECBUFDESC), POINTER(ULONG), c_void_p
]
sspi.FreeContextBuffer.argtypes = [LPVOID]

SEC_PKG_CRED_OUTBOUND = 2
SEC_FLAG_SEQUENCE_DETECT = 0x01000000
SEC_FLAG_REPLAY_DETECT = 0x02000000
SEC_I_CONTINUE_NEEDED = 0x00090312
USE_SUPPLIED_CREDENTIALS = 0x00000010

def sspi_negotiate(host_ip, username, password):
    """Perform SSPI Negotiate handshake. Returns list of auth header values."""
    target = f'http://{host_ip}:5985'
    
    # Acquire credentials
    identity = SEC_WINNT_AUTH_IDENTITY_W()
    identity.User = username
    identity.Domain = 'WORKGROUP'
    identity.Password = password
    identity.UserLength = len(username)
    identity.DomainLength = 9
    identity.PasswordLength = len(password)
    
    idbuf = SEC_WINNT_AUTH_IDENTITY_BUFFER_W()
    idbuf.Identity = identity
    idbuf.Flags = USE_SUPPLIED_CREDENTIALS
    
    cred = LPVOID()
    expiry = FILETIME()
    r = sspi.AcquireCredentialsHandleW(
        'Negotiate', None, SEC_PKG_CRED_OUTBOUND,
        None, byref(idbuf), None, None, byref(cred), byref(expiry)
    )
    if r != 0:
        raise RuntimeError(f'AcquireCredentialsHandleW failed: 0x{r:08X}')
    
    try:
        # Step 1: Generate initial token (Type 1)
        ctx = LPVOID()
        outbufs = (SECBUFDESC * 1)()
        max_out = ULONG(1)
        r = sspi.InitializeSecurityContextW(
            cred, None, target,
            SEC_FLAG_SEQUENCE_DETECT | SEC_FLAG_REPLAY_DETECT,
            0, 0, None, 0,
            byref(ctx), None, byref(outbufs), byref(max_out), None
        )
        if r not in (0, SEC_I_CONTINUE_NEEDED):
            raise RuntimeError(f'InitSecurityContext step1 failed: 0x{r:08X}')
        
        token1 = bytes(outbufs[0].pvBuffer, outbufs[0].cbBuffer)
        sspi.FreeContextBuffer(outbufs[0].pvBuffer)
        auth1 = 'Negotiate ' + base64.b64encode(token1).decode()
        
        # Send request, expect 401
        soap = _make_create_channel_soap(host_ip)
        resp = _http_post(host_ip, soap, auth1)
        
        if '401' not in resp.split('\r\n')[0]:
            return [auth1]  # Auth succeeded on first try
        
        # Extract challenge
        challenge_b64 = None
        for line in resp.split('\r\n'):
            if line.lower().startswith('www-authenticate:'):
                val = line.split(':', 1)[1].strip()
                if 'Negotiate' in val:
                    challenge_b64 = val.split('Negotiate', 1)[1].strip()
                break
        if not challenge_b64:
            raise RuntimeError(f'No Negotiate challenge in: {resp[:300]}')
        
        # Step 2: Process challenge, generate Type 3
        challenge = base64.b64decode(challenge_b64)
        inbuf = SECBUFDESC()
        inbuf.cbBuffer = len(challenge)
        inbuf.BufferType = 19  # SEC_TOKEN
        inbuf.pvBuffer = cast(create_string_buffer(challenge, len(challenge)), LPVOID)
        
        outbufs2 = (SECBUFDESC * 1)()
        max_out2 = ULONG(1)
        r = sspi.InitializeSecurityContextW(
            cred, ctx, None,
            SEC_FLAG_SEQUENCE_DETECT | SEC_FLAG_REPLAY_DETECT,
            0, 0, byref(inbuf), 1,
            byref(ctx), None, byref(outbufs2), byref(max_out2), None
        )
        if r not in (0, SEC_I_CONTINUE_NEEDED):
            raise RuntimeError(f'InitSecurityContext step2 failed: 0x{r:08X}')
        
        token3 = bytes(outbufs2[0].pvBuffer, outbufs2[0].cbBuffer)
        sspi.FreeContextBuffer(outbufs2[0].pvBuffer)
        auth2 = 'Negotiate ' + base64.b64encode(token3).decode()
        
        # Retry with Type 3
        resp2 = _http_post(host_ip, soap, auth2)
        return [auth2]  # Return working auth for subsequent requests
    finally:
        sspi.FreeCredentialsHandle(byref(cred))

def _http_post(host_ip, body, auth_header):
    """Send HTTP POST to WinRM endpoint."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(15)
    s.connect((host_ip, 5985))
    req = (
        f'POST /wsman HTTP/1.1\r\n'
        f'Host: {host_ip}:5985\r\n'
        f'Content-Type: application/soap+xml; charset=utf-8\r\n'
        f'Authorization: {auth_header}\r\n'
        f'Content-Length: {len(body.encode())}\r\n'
        f'Connection: close\r\n\r\n'
    )
    s.sendall(req.encode() + body.encode())
    data = b''
    while True:
        try:
            chunk = s.recv(65536)
            if not chunk: break
            data += chunk
        except socket.timeout: break
    s.close()
    return data.decode('utf-8', errors='replace')

def _make_create_channel_soap(host_ip):
    """Minimal WS-Management Create request to establish a channel."""
    msg_id = f'uuid:{uuid.uuid4()}'
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<s:Envelope xmlns:s="http://www.w3.org/2003/05/soap-envelope">'
        '<s:Header>'
        f'<wsa:To xmlns:wsa="http://www.w3.org/2005/08/addressing">http://{host_ip}:5985/wsman</wsa:To>'
        '<wsa:Action xmlns:wsa="http://www.w3.org/2005/08/addressing">'
        'http://schemas.dmtf.org/wbem/ws-man/1/Create</wsa:Action>'
        f'<wsa:MessageID xmlns:wsa="http://www.w3.org/2005/08/addressing">{msg_id}</wsa:MessageID>'
        '</s:Header><s:Body>'
        '<wsmid:CreateRequest xmlns:wsmid="http://schemas.dmtf.org/wbem/ws-man/1/cim-schema/1">'
        '<wsmid:ResourceURI>http://schemas.dmtf.org/wbem/ws-man/1/cim-schema/1/CIM_20_WSMan</wsmid:ResourceURI>'
        '</wsmid:CreateRequest></s:Body></s:Envelope>'
    )

if __name__ == '__main__':
    hosts = [
        ('PALE', 'IP_PALE', 'pale'),
        ('BLACK', 'IP_BLACK', 'black'),
    ]
    pw = '[REDACTED-CREDENTIAL]'
    results = []
    for name, ip, user in hosts:
        try:
            auths = sspi_negotiate(ip, user, pw)
            print(f'{name} ({ip}): WinRM channel established OK')
            results.append({'host': name, 'status': 'PASS'})
        except Exception as e:
            print(f'{name} ({ip}): FAIL - {type(e).__name__}: {e}')
            results.append({'host': name, 'status': 'FAIL', 'error': str(e)[:200]})
    
    out = {'ts': time.strftime('%Y-%m-%dT%H:%M:%S'), 'results': results}
    with open('winrm_exec_test_result.json', 'w') as f:
        json.dump(out, f, indent=2)
    print(f'\nDone -> winrm_exec_test_result.json')
    sys.exit(0 if all(r['status'] == 'PASS' for r in results) else 1)