"""
winrm_sspi_exec.py - Minimal WinRM auth test via Windows SSPI (ctypes).
No external deps. Tests NTLM auth to PALE from sandbox.
Usage: python memory/mechanic/winrm_sspi_exec.py
"""
import socket, uuid, base64, sys, gc
from ctypes import *

class SEC_WINNT_AUTH_IDENTITY_W(Structure):
    _fields_ = [
        ('User', c_wchar_p), ('UserLength', c_ushort),
        ('Domain', c_wchar_p), ('DomainLength', c_ushort),
        ('Password', c_wchar_p), ('PasswordLength', c_ushort),
    ]

class SECBUFDESC(Structure):
    _fields_ = [('cbBuffer', c_ulong), ('BufferType', c_int), ('pvBuffer', c_void_p)]

class SECURITY_CONTEXT_ATTRIBUTES(Structure):
    _fields_ = [
        ('dwLength', c_ulong), ('fContextAttribute', c_ulong),
        ('Reserved', c_void_p), ('hToken', c_void_p),
        ('pTiedInfo', c_void_p), ('KiLMode', c_ulong), ('dwFlags', c_ulong),
    ]

SECPKG_CRED_OUTBOUND = 2
SEC_FLAG_SEQUENCE_DETECT = 0x01000000
SEC_FLAG_REPLAY_DETECT = 0x02000000
SEC_OK = 0
SEC_I_CONTINUE_NEEDED = 0x00090312

sspi = windll.secur32

def acquire_creds(user, domain, password):
    # Build identity with explicit c_wchar_p pointers
    user_c = cast(create_unicode_buffer(user), c_wchar_p)
    domain_c = cast(create_unicode_buffer(domain), c_wchar_p) if domain else None
    pw_c = cast(create_unicode_buffer(password), c_wchar_p) if password else None
    
    identity = SEC_WINNT_AUTH_IDENTITY_W()
    identity.User = user_c
    identity.Domain = domain_c
    identity.Password = pw_c
    identity.UserLength = len(user)
    identity.DomainLength = len(domain) if domain else 0
    identity.PasswordLength = len(password) if password else 0
    
    cred_handle = c_void_p()
    expiry = c_ulonglong(0)
    
    r = sspi.AcquireCredentialsHandleW(
        None, 'Negotiate', SECPKG_CRED_OUTBOUND,
        None, byref(identity), None, None,
        byref(cred_handle), byref(expiry))
    
    if r != SEC_OK:
        raise RuntimeError("AcquireCredentialsHandleW failed: 0x%08X" % (r & 0xFFFFFFFF))
    return cred_handle

def sspi_negotiate(cred_handle, target):
    context = c_void_p()
    attrs = SECURITY_CONTEXT_ATTRIBUTES()
    attrs.dwLength = sizeof(attrs)
    out_bufs = (SECBUFDESC * 1)()
    r = sspi.InitializeSecurityContextW(
        byref(cred_handle), None, target.encode('utf-16-le'),
        SEC_FLAG_SEQUENCE_DETECT | SEC_FLAG_REPLAY_DETECT,
        0, 0, None, 0,
        byref(context), byref(attrs), byref(out_bufs), c_ulong(1), None)
    if r not in (SEC_OK, SEC_I_CONTINUE_NEEDED):
        raise RuntimeError("SSPI step1 failed: 0x%08X" % (r & 0xFFFFFFFF))
    token1 = bytes(out_bufs[0].pvBuffer, out_bufs[0].cbBuffer)
    sspi.FreeContextBuffer(out_bufs[0].pvBuffer)
    return token1, context, attrs

def sspi_challenge(cred_handle, context, attrs, challenge_b64):
    challenge = base64.b64decode(challenge_b64)
    in_buf = SECBUFDESC()
    in_buf.cbBuffer = len(challenge)
    in_buf.BufferType = 19
    in_buf.pvBuffer = cast(create_string_buffer(challenge, len(challenge)), c_void_p)
    in_bufs = (SECBUFDESC * 1)(in_buf)
    out_bufs = (SECBUFDESC * 1)()
    r = sspi.InitializeSecurityContextW(
        byref(cred_handle), context, None,
        SEC_FLAG_SEQUENCE_DETECT | SEC_FLAG_REPLAY_DETECT,
        0, 0, in_bufs, 1,
        byref(context), byref(attrs), byref(out_bufs), c_ulong(1), None)
    if r not in (SEC_OK, SEC_I_CONTINUE_NEEDED):
        raise RuntimeError("SSPI step2 failed: 0x%08X" % (r & 0xFFFFFFFF))
    token = bytes(out_bufs[0].pvBuffer, out_bufs[0].cbBuffer)
    sspi.FreeContextBuffer(out_bufs[0].pvBuffer)
    return token

def http_post(host_ip, soap_body, auth_header=None):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(30)
    s.connect((host_ip, 5985))
    req = "POST /wsman HTTP/1.1\r\nHost: %s:5985\r\nContent-Type: application/soap+xml; charset=utf-8\r\n" % host_ip
    if auth_header:
        req += "Authorization: %s\r\n" % auth_header
    req += "Content-Length: %d\r\nConnection: close\r\n\r\n%s" % (len(soap_body), soap_body)
    s.sendall(req.encode())
    data = b''
    while True:
        try:
            chunk = s.recv(8192)
            if not chunk: break
            data += chunk
        except socket.timeout: break
    s.close()
    text = data.decode('utf-8', errors='replace')
    parts = text.split('\r\n\r\n', 1)
    headers_raw = parts[0]
    body = parts[1] if len(parts) > 1 else ''
    lines = headers_raw.split('\r\n')
    status_code = int(lines[0].split()[1])
    headers = {}
    for line in lines[1:]:
        if ':' in line:
            k, v = line.split(':', 1)
            headers[k.strip().lower()] = v.strip()
    return status_code, headers, body

def test_auth():
    host_ip = "IP_PALE"
    user, domain, password = "pale", "WORKGROUP", "[REDACTED-CREDENTIAL]"
    target = "http://%s:5985" % host_ip

    print("[1] Acquiring SSPI credentials...")
    cred_handle = acquire_creds(user, domain, password)
    print("  OK")

    print("[2] Generating Type 1 token...")
    token1, context, attrs = sspi_negotiate(cred_handle, target)
    auth1 = "Negotiate " + base64.b64encode(token1).decode()
    print("  Token len=%d" % len(token1))

    print("[3] Sending Create request with Type 1...")
    msg_id = str(uuid.uuid4())
    soap = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<s:Envelope xmlns:s="http://www.w3.org/2003/05/soap-envelope">'
        '<s:Header><wsa:To xmlns:wsa="http://www.w3.org/2005/08/addressing">http://%s:5985/wsman</wsa:To>'
        '<wsa:Action xmlns:wsa="http://www.w3.org/2005/08/addressing">http://schemas.dmtf.org/wbem/ws-man/1/Create</wsa:Action>'
        '<wsa:MessageID xmlns:wsa="http://www.w3.org/2005/08/addressing">uuid:%s</wsa:MessageID></s:Header><s:Body>'
        '<wsmid:CreateRequest xmlns:wsmid="http://schemas.dmtf.org/wbem/ws-man/1/cim-schema/1">'
        '<wsmid:ResourceURI>http://schemas.dmtf.org/wbem/ws-man/1/cim-schema/1/CIM_20_WSMan</wsmid:ResourceURI>'
        '</wsmid:CreateRequest></s:Body></s:Envelope>' % (host_ip, msg_id))

    status, headers, body = http_post(host_ip, soap, auth1)
    print("  Status: %d" % status)

    if status == 401:
        challenge = headers.get("www-authenticate", "")
        print("[4] Got 401, challenge present: %s" % bool(challenge))
        if "Negotiate " in challenge:
            ch_b64 = challenge.split("Negotiate ", 1)[1].strip()
        else:
            raise RuntimeError("No Negotiate challenge in: %s" % challenge[:100])

        token2 = sspi_challenge(cred_handle, context, attrs, ch_b64)
        auth2 = "Negotiate " + base64.b64encode(token2).decode()
        print("  Type 3 token len=%d" % len(token2))

        print("[5] Retrying with Type 3...")
        status, headers, body = http_post(host_ip, soap, auth2)
        print("  Status: %d" % status)

    sspi.FreeCredentialsHandle(byref(cred_handle))

    if status == 200:
        print("\n[PASS] SSPI NTLM auth works from sandbox!")
        return True
    else:
        print("\n[FAIL] Final status: %d" % status)
        print("Body: %s" % body[:300])
        return False

if __name__ == "__main__":
    try:
        ok = test_auth()
        sys.exit(0 if ok else 1)
    except Exception as e:
        print("ERROR: %s: %s" % (type(e).__name__, e))
        sys.exit(2)
