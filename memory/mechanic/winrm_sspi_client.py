"""
WinRM client using Windows SSPI (secur32.dll) for Negotiate/NTLM auth.
Run from White terminal: python memory/mechanic/winrm_sspi_client.py
No external dependencies - uses ctypes + socket only.
"""
import socket, struct, uuid, time, json, sys
from ctypes import *

# --- SSPI structures ---
class SEC_WINNT_AUTH_IDENTITY_W(Structure):
    _fields_ = [
        ('User', c_wchar_p),
        ('UserLength', c_ushort),
        ('Domain', c_wchar_p),
        ('DomainLength', c_ushort),
        ('Password', c_wchar_p),
        ('PasswordLength', c_ushort),
    ]

class SEC_WINNT_AUTH_IDENTITY_BUFFER_W(Structure):
    _fields_ = [
        ('Identity', SEC_WINNT_AUTH_IDENTITY_W),
        ('Flags', c_ulong),
    ]

class SECBUFDESC(Structure):
    _fields_ = [('cbBuffer', c_ulong), ('BufferType', c_int), ('pvBuffer', c_void_p)]

class SECURITY_CONTEXT_ATTRIBUTES(Structure):
    _fields_ = [
        ('dwLength', c_ulong),
        ('fContextAttribute', c_ulong),
        ('Reserved', c_void_p),
        ('hToken', c_void_p),
        ('pTiedInfo', c_void_p),
        ('KiLMode', c_ulong),
        ('dwFlags', c_ulong),
    ]

IS_NAMED_PIPE = 0x00000100
SECPKG_CRED_OUTBOUND = 2
SEC_FLAG_SEQUENCE_DETECT = 0x01000000
SEC_FLAG_REPLAY_DETECT = 0x02000000
SEC_INBOUND = 0
SEC_OUTBOUND = 1
SEC_OK = 0
SEC_I_CONTINUE_NEEDED = 0x00090312
SEC_E_INSUFFICIENT_MEMORY = 0x80090301

# Load secur32
sspi = windll.secur32 if hasattr(windll, 'secur32') else CDLL('secur32.dll')

def acquire_credentials(username, password):
    """Acquire a credentials handle for WinRM (Negotiate)."""
    identity = SEC_WINNT_AUTH_IDENTITY_W()
    identity.User = username.encode('utf-16-le') or None
    identity.Domain = 'WORKGROUP'.encode('utf-16-le') if not username.startswith('\\') else None
    identity.Password = password.encode('utf-16-le') or None
    identity.UserLength = len(username) if username else 0
    identity.DomainLength = 9  # WORKGROUP
    identity.PasswordLength = len(password)
    
    identity_buffer = SEC_WINNT_AUTH_IDENTITY_BUFFER_W()
    identity_buffer.Identity = identity
    identity_buffer.Flags = 0x00000010  # USE_SUPPLIED_CREDENTIALS
    
    cred_handle = c_void_p()
    expiry = FILETIME()
    
    result = sspi.AcquireCredentialsHandleW(
        None,           # package name (NULL = all)
        'Negotiate',    # package
        SECPKG_CRED_OUTBOUND,
        None,           # logon user
        byref(identity_buffer),  # auth data
        None,           # get key fn
        None,           # get key arg
        byref(cred_handle),
        byref(expiry)
    )
    if result != SEC_OK:
        raise RuntimeError(f"AcquireCredentialsHandleW failed: 0x{result:08X}")
    return cred_handle

def free_credentials(cred_handle):
    sspi.FreeCredentialsHandle(byref(cred_handle))

def negotiate(cred_handle, target):
    """
    Perform the full Negotiate/NTLM handshake.
    Returns list of (auth_header_value) for each round.
    For HTTP: first token goes in initial request, second in retry.
    """
    # Step 1: Initialize with no input to get Type 1 message
    context = c_void_p()
    attrs = SECURITY_CONTEXT_ATTRIBUTES()
    attrs.dwLength = sizeof(attrs)
    
    out_bufs = (SECBUFDESC * 1)()
    in_bufs = (SECBUFDESC * 0)()  # no input for first call
    
    # First call: generate initial token
    result = sspi.InitializeSecurityContextW(
        byref(cred_handle),   # CredentialsHandle
        None,                 # PreviousContext (None for first)
        target.encode('utf-16-le'),  # Target (e.g., 'http://host:5985')
        SEC_FLAG_SEQUENCE_DETECT | SEC_FLAG_REPLAY_DETECT,
        0,                    # Reserved
        0,                    # Local RPC ID
        None,                 # Input buffers (none)
        0,                    # Input buffer count
        byref(context),       # Output context
        byref(attrs),         # Context attrs
        byref(out_bufs),      # Output buffers
        c_ulong(1),           # Max output buffer count
        None                  # Time stamp (unused)
    )
    
    if result not in (SEC_OK, SEC_I_CONTINUE_NEEDED):
        raise RuntimeError(f"InitializeSecurityContextW (step 1) failed: 0x{result:08X}")
    
    token1 = bytes(out_bufs[0].pvBuffer, out_bufs[0].cbBuffer)
    sspi.FreeContextBuffer(out_bufs[0].pvBuffer)
    
    # For HTTP Negotiate: the first token is the Type 1 (negotiate) message
    # The server will respond with a 401 containing the Type 2 (challenge)
    # We then need to process that challenge and generate Type 3 (authenticate)
    
    return token1, context, attrs

def process_challenge(cred_handle, context, attrs, challenge_token):
    """Process server's challenge (Type 2) and produce response (Type 3)."""
    in_buf = SECBUFDESC()
    in_buf.cbBuffer = len(challenge_token)
    in_buf.BufferType = 19  # SEC_TOKEN
    in_buf.pvBuffer = cast(create_string_buffer(challenge_token, len(challenge_token)), c_void_p)
    
    in_bufs = (SECBUFDESC * 1)(in_buf)
    out_bufs = (SECBUFDESC * 1)()
    
    result = sspi.InitializeSecurityContextW(
        byref(cred_handle),
        context,              # Previous context
        None,                 # Target (already set)
        SEC_FLAG_SEQUENCE_DETECT | SEC_FLAG_REPLAY_DETECT,
        0,
        0,
        in_bufs,
        1,
        byref(context),       # Update context
        byref(attrs),
        byref(out_bufs),
        c_ulong(1),
        None
    )
    
    if result not in (SEC_OK, SEC_I_CONTINUE_NEEDED):
        raise RuntimeError(f"InitializeSecurityContextW (step 2) failed: 0x{result:08X}")
    
    token2 = bytes(out_bufs[0].pvBuffer, out_bufs[0].cbBuffer)
    sspi.FreeContextBuffer(out_bufs[0].pvBuffer)
    return token2

def winrm_request(host_ip, username, password, soap_body):
    """Make a WinRM request with proper Negotiate auth."""
    target = f"http://{host_ip}:5985"
    cred_handle = acquire_credentials(username, password)
    
    try:
        # Get initial token (Type 1)
        token1, context, attrs = negotiate(cred_handle, target)
        import base64
        auth1 = 'Negotiate ' + base64.b64encode(token1).decode()
        
        # Send first request with Type 1
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(15)
        s.connect((host_ip, 5985))
        
        req = (
            f"POST /wsman HTTP/1.1\r\n"
            f"Host: {host_ip}:5985\r\n"
            f"Content-Type: application/soap+xml; charset=utf-8\r\n"
            f"Authorization: {auth1}\r\n"
            f"Content-Length: {len(soap_body)}\r\n"
            f"Connection: close\r\n\r\n"
            f"{soap_body}"
        )
        s.sendall(req.encode())
        
        # Read response
        resp_data = b''
        while True:
            try:
                chunk = s.recv(4096)
                if not chunk: break
                resp_data += chunk
            except socket.timeout: break
        s.close()
        
        resp_text = resp_data.decode('utf-8', errors='replace')
        status_line = resp_text.split('\r\n')[0]
        
        # If 401, extract challenge and retry with Type 3
        if '401' in status_line:
            # Find the WWW-Authenticate header value
            for line in resp_text.split('\r\n'):
                if line.lower().startswith('www-authenticate:'):
                    challenge_b64 = line.split(':', 1)[1].strip()
                    if challenge_b64.startswith('Negotiate '):
                        challenge_b64 = challenge_b64[len('Negotiate '):]
                    break
            else:
                raise RuntimeError(f"No WWW-Authenticate header found in: {resp_text[:200]}")
            
            import base64
            challenge_token = base64.b64decode(challenge_b64)
            token2 = process_challenge(cred_handle, context, attrs, challenge_token)
            auth2 = 'Negotiate ' + base64.b64encode(token2).decode()
            
            # Retry with Type 3
            s2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s2.settimeout(15)
            s2.connect((host_ip, 5985))
            req2 = (
                f"POST /wsman HTTP/1.1\r\n"
                f"Host: {host_ip}:5985\r\n"
                f"Content-Type: application/soap+xml; charset=utf-8\r\n"
                f"Authorization: {auth2}\r\n"
                f"Content-Length: {len(soap_body)}\r\n"
                f"Connection: close\r\n\r\n"
                f"{soap_body}"
            )
            s2.sendall(req2.encode())
            resp_data2 = b''
            while True:
                try:
                    chunk = s2.recv(4096)
                    if not chunk: break
                    resp_data2 += chunk
                except socket.timeout: break
            s2.close()
            return resp_data2.decode('utf-8', errors='replace')
        
        return resp_text
    finally:
        free_credentials(cred_handle)

# --- Test: WinRM Create on Pale ---
if __name__ == '__main__':
    soap = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<s:Envelope xmlns:s="http://www.w3.org/2003/05/soap-envelope">'
        '<s:Header>'
        '<wsa:To xmlns:wsa="http://www.w3.org/2005/08/addressing">http://192.168.1.39:5985/wsman</wsa:To>'
        '<wsa:Action xmlns:wsa="http://www.w3.org/2005/08/addressing">'
        'http://schemas.dmtf.org/wbem/ws-man/1/Create</wsa:Action>'
        f'<wsa:MessageID xmlns:wsa="http://www.w3.org/2005/08/addressing">uuid:{uuid.uuid4()}</wsa:MessageID>'
        '</s:Header><s:Body>'
        '<wsmid:CreateRequest xmlns:wsmid="http://schemas.dmtf.org/wbem/ws-man/1/cim-schema/1">'
        '<wsmid:ResourceURI>http://schemas.dmtf.org/wbem/ws-man/1/cim-schema/1/CIM_20_WSMan</wsmid:ResourceURI>'
        '</wsmid:CreateRequest></s:Body></s:Envelope>'
    )
    
    print("=== WinRM SSPI Test: Pale 192.168.1.39 ===")
    try:
        resp = winrm_request('192.168.1.39', 'pale', '131991Apiet', soap)
        print(f"Response ({len(resp)} bytes):")
        print(resp[:800])
    except Exception as e:
        print(f"ERROR: {type(e).__name__}: {e}")
