css = open('ui/app.css').read()
L = css.splitlines()
targets = ['#e05252', '#4f8cff', '#2ecc71']
for t in targets:
    print('=== ', t)
    for i, l in enumerate(L):
        if t in l:
            print(i + 1, ':', l.strip()[:170])
