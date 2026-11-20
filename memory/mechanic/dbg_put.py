import winrm, base64
s = winrm.Session('http://IP_PALE:5985/wsman', auth=('pale', ''), transport='ntlm',
              operation_timeout_sec=60, read_timeout_sec=180)
content = open('memory/mechanic/launcher_PALE.txt', encoding='utf-8').read().strip()
b = base64.b64encode(content.encode('utf-8')).decode()
ps = "Set-Content -Path C:/FleetOps/x.b64 -Value '" + b + "' -Encoding ASCII; certutil -decode C:/FleetOps/x.b64 C:/FleetOps/studio_launch.txt"
r = s.run_ps(ps)
print('OUT:', repr(r.std_out.decode()[:200]))
print('ERR:', repr(r.std_err.decode()[:200]))
