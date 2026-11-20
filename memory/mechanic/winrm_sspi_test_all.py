"""WinRM SSPI probe using ctypes with proper restype: test PALE + BLACK."""
import socket, uuid, base64, json
from ctypes import *

sspi = CDLL('secur32.dll')
sspi.AcquireCredentialsHandleW.restype = c_ulong
sspi.InitializeSecurityContextW.restype = c_ulong
sspi.FreeCredentialsHandle.restype = c_ulong
sspi.FreeContextBuffer.restype = None

class FILETIME(Structure):
    _fields_ = [('dwLowDateTime', c_ulong), ('dwHighDateTime', c_ulong)]

class SEC_WINNT_AUTH_IDENTITY_W(Structure):
    _fields_ = [
        ('User', c_wchar_p), ('UserLength', c_ushort),
        ('Domain', c_wchar_p), ('DomainLength', c_ushort),
        ('Password', c_wchar_p), ('PasswordLength', c_ushort),
    ]

class SECBUFFER(Structure):
    _fields_ = [('cbBuffer', c_ulong), ('BufferType', c_int), ('pvBuffer', c_void_p)]

class SEC_BUFFER_DESC(Structure):
    _fields_ = [('ulVersion', c_ulong), ('cBuffers', c_ulong), ('pBuffers', POINTER(SECBUFFER))]

SECPKG_CRED_OUTBOUND = 2
ISC_REQ_SEQ = 0x01000000
ISC_REQ_REPLAY = 0x02000000
SEC_OK = 0
SEC_I_CONTINUE_NEEDED = 0x00090312

SOAP_CREATE = (
    '<?xml version="1.0" encoding="UTF-8"?>'
    '<s:Envelope xmlns:s="http://www.w3.org/2003/05/soap-envelope">'
    '<s:Header>'
    '<wsa:To xmlns:wsa="http://www.w3.org/2005/08/addressing">{target}/wsman</wsa:To>'
    '<wsa:Action xmlns:wsa="http://www.w3.org/2005/08/addressing">'
    'http://schemas.dmtf.org/wbem/ws-man/1/Create</wsa:Action>'
    '<wsa:MessageID xmlns:wsa="http://www.w3.org/2005/08/addressing">uuid:{msgid}</wsa:MessageID>'
    '</s:Header><s:Body>'
    '<wsmid:CreateRequest xmlns:wsmid="http://schemas.dmtf.org/wbem/ws-man/1/cim-schema/1">'
    '<wsmid:ResourceURI>http://schemas.dmtf.org/wbem/ws-man/1/cim-schema/1/CIM_20_WSMan</wsmid:ResourceURI>'
    '</wsmid:CreateRequest></s:Body></s:Envelope>'
)

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
        except: break
        if not c: break
        rd += c
    s.close()
    return rd.decode('utf-8', 'replace')

def parse_status(resp):
    return resp.split('\r\n')[0]

def get_challenge(resp):
    for ln in resp.split('\r\n'):
        if ln.lower().startswith('www-authenticate:'):
            val = ln.split(':', 1)[1].strip()
            if val.startswith('Negotiate '):
                return val[10:]
            return val
    return None

def acquire_cred(user, pw):
    ubuf = create_unicode_buffer(user)
    dbuf = create_unicode_buffer('WORKGROUP')
    pbuf = create_unicode_buffer(pw) if pw else None
    
    ident = SEC_WINNT_AUTH_IDENTITY_W()
    ident.User = cast(ubuf, c_wchar_p)
    ident.UserLength = len(user)
    ident.Domain = cast(dbuf, c_wchar_p)
    ident.DomainLength = 9
    if pbuf:
        ident.Password = cast(pbuf, c_wchar_p)
        ident.PasswordLength = len(pw)
    else:
        ident.Password = None
        ident.PasswordLength = 0
    
    cred = c_void_p()
    expiry = FILETIME()
    
    # Pass NULL for auth_data to use default (current user) credentials
    # OR pass the identity buffer. Let's try with identity first.
    r = sspi.AcquireCredentialsHandleW(
        'Negotiate',  # package
        None,         # auth type
        SECPKG_CRED_OUTBOUND,
        None,         # logon id
        byref(ident),  # auth data (SEC_WINNT_AUTH_IDENTITY_W)
        None,         # get key fn
        None          # get key arg
    )
    if r != SEC_OK:
        raise RuntimeError('AcquireCredentialsHandleW failed: 0x%08X' % r)
    return cred, (ubuf, dbuf, pbuf)

def init_sec_ctx(cred, prev_ctx, target, input_token):
    """Perform InitializeSecurityContextW. Returns (status, new_context, output_token)."""
    ctx = c_void_p() if not prev_ctx else prev_ctx
    
    # Input buffers
    in_buf = SECBUFFER()
    in_desc = SEC_BUFFER_DESC()
    in_desc.ulVersion = 0
    in_desc.cBuffers = 1
    in_desc.pBuffers = pointer(in_buf)
    
    if input_token:
        buf_mem = create_string_buffer(input_token, len(input_token))
        in_buf.cbBuffer = len(input_token)
        in_buf.BufferType = 19  # SEC_TOKEN
        in_buf.pvBuffer = cast(buf_mem, c_void_p)
    else:
        in_desc.cBuffers = 0
    
    # Output buffers
    out_buf = SECBUFFER()
    out_desc = SEC_BUFFER_DESC()
    out_desc.ulVersion = 0
    out_desc.cBuffers = 1
    out_desc.pBuffers = pointer(out_buf)
    
    flags = ISC_REQ_SEQ | ISC_REQ_REPLAY
    
    if input_token:
        r = sspi.InitializeSecurityContextW(
            byref(cred), byref(ctx), None,
            flags, 0, 0,
            byref(in_desc), 1,
            byref(ctx), None,
            byref(out_desc), None
        )
    else:
        r = sspi.InitializeSecurityContextW(
            byref(cred), None, target,
            flags, 0, 0,
            None, 0,
            byref(ctx), None,
            byref(out_desc), None
        )
    
    if r not in (SEC_OK, SEC_I_CONTINUE_NEEDED):
        raise RuntimeError('InitializeSecurityContextW failed: 0x%08X' % r)
    
    token = bytes(out_buf.pvBuffer, out_buf.cbBuffer) if out_buf.cbBuffer else b''
    sspi.FreeContextBuffer(out_buf.pvBuffer)
    return r, ctx, token

def test_host(ip, user, pw):
    target = 'http://%s:5985' % ip
    
    try:
        cred, bufs = acquire_cred(user, pw)
    except Exception as e:
        return 'AcquireCred: %s' % e
    
    try:
        # Step 1: Generate Type 1 (negotiate) token
        status, ctx, t1 = init_sec_ctx(cred, None, target, None)
        a1 = 'Negotiate ' + base64.b64encode(t1).decode()
        
        # Send initial request with Type 1
        msgid = str(uuid.uuid4())
        soap = SOAP_CREATE.format(target=target, msgid=msgid)
        resp = http_post(ip, '/wsman', {
            'Content-Type': 'application/soap+xml; charset=utf-8',
            'Authorization': a1
        }, soap.encode())
        
        sl = parse_status(resp)
        if '401' not in sl:
            ok = 'CreateResponse' in resp or 'cim-schema' in resp or '200' in sl
            return '%s | ok=%s | size=%d' % (sl, ok, len(resp))
        
        # Step 2: Process challenge -> Type 3
        cb64 = get_challenge(resp)
        if not cb64:
            return '401 no challenge token in: %s' % resp[:200]
        ctok = base64.b64decode(cb64)
        
        status2, ctx2, t2 = init_sec_ctx(cred, ctx, target, ctok)
        a2 = 'Negotiate ' + base64.b64encode(t2).decode()
        
        # Retry with Type 3
        resp2 = http_post(ip, '/wsman', {
            'Content-Type': 'application/soap+xml; charset=utf-8',
            'Authorization': a2
        }, soap.encode())
        sl2 = parse_status(resp2)
        ok = 'CreateResponse' in resp2 or 'cim-schema' in resp2 or '200' in sl2
        return '%s | ok=%s | size=%d' % (sl2, ok, len(resp2))
    except Exception as e:
        return '%s: %s' % (type(e).__name__, e)
    finally:
        sspi.FreeCredentialsHandle(byref(cred))

results = {}
for name, ip, user, pw in [('PALE', 'IP_PALE', 'pale', ''), ('BLACK', 'IP_BLACK', 'black', '')]:
    results[name] = test_host(ip, user, pw)
print(json.dumps(results, indent=2))
