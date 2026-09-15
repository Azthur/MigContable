import re
h = open('/app/informe_migracion.html', encoding='utf-8').read()
bloques = re.split(r'<div class="empresa"><h2>', h)[1:]
for b in bloques:
    titulo = re.match(r'(Empresa \d+: [^<]+)', b)
    if not titulo:
        continue
    kpis = re.findall(r'<div class="v[^"]*">([^<]+)</div><div class="l">([^<]+)</div>', b)
    print(titulo.group(1))
    for v, l in kpis:
        print(f'   {l}: {v}')
    print()
