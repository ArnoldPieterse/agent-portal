import winrm
s = winrm.Session('http://IP_PALE:5985/wsman', auth=('pale', ''), transport='ntlm',
              operation_timeout_sec=60, read_timeout_sec=180)
r = s.run_ps('(Get-Process -Id 19992).Path')
print(r.std_out.decode().strip())
