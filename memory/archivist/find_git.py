import os, time

t0 = time.time()
found = []
prune = {"windows", "recycler", "$recycle.bin", "node_modules", "microsoft", "cache"}
for root, dirs, files in os.walk("C:\\"):
    if time.time() - t0 > 45:
        break
    dirs[:] = [d for d in dirs if d.lower() not in prune]
    if "git.exe" in files and ("mingw64" in root.lower() or "cmd" in root.lower() or "bin" in root.lower()):
        found.append(os.path.join(root, "git.exe"))
        if len(found) >= 4:
            break
for f in found:
    print(f)
print("scan done", len(found))
