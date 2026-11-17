"""Raw WinRM HTTP test via socket - run from White terminal (not sandbox)."""
import socket, base64, sys

def winrm_create_session(host_ip, user, password):
    soap = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<s:Envelope xmlns:s="http://www.w3.org/2003/05/soap-envelope">'
        f'<s:Header>'
        f'<wsa:To xmlns:wsa="http://www.w3.org/2005/08/addressing">http://{host_ip}:5985/wsman</wsa:To>'
        '<wsa:Action xmlns:wsa="http://www.w3.org/2005/08/addressing">'
        'http://schemas.dmtf.org/wbem/ws-man/1/Create</wsa:Action>'
        '<wsa:MessageID xmlns:wsa="http://www.w3.org/2005/08/addressing">uuid:pale-test-001</wsa:MessageID>'
        '</s:Header>'
        '<s:Body>'
        '<wsmid:CreateRequest xmlns:wsmid="http://schemas.dmtf.org/wbem/ws-man/1/cim-schema/1">'
        '<wsmid:ResourceURI>http://schemas.dmtf.org/wbem/ws-man/1/cim-schema/1/CIM_20_WSMan</wsmid:ResourceURI>'
        '</wsmid:CreateRequest>'
        '</s:Body></s:Envelope>'
    )
    auth = base64.b64encode(f"{user}:{password}".encode()).decode()
    req = (
        f"POST /wsman HTTP/1.1\r\n"
        f"Host: {host_ip}:5985\r\n"
        f"Content-Type: application/soap+xml; charset=utf-8\r\n"
        f"Authorization: Basic {auth}\r\n"
        f"Content-Length: {len(soap)}\r\n"
        f"Connection: close\r\n\r\n"
        f"{soap}"
    )
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(15)
    s.connect((host_ip, 5985))
    s.sendall(req.encode())
    chunks = []
    while True:
        try:
            chunk = s.recv(4096)
            if not chunk:
                break
            chunks.append(chunk)
        except socket.timeout:
            break
    s.close()
    return b''.join(chunks).decode('utf-8', errors='replace')

if __name__ == '__main__':
    print("Testing Pale .39 WinRM...")
    resp = winrm_create_session('IP_PALE', 'pale', '[REDACTED-CREDENTIAL]')
    print(f"Response ({len(resp)} bytes):")
    print(resp[:1000])
