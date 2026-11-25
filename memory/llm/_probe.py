t = open("agent_portal.py", encoding="utf-8").read().splitlines()
for i in range(6924, 6937):
    print(i + 1, t[i][:75])