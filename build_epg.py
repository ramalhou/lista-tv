#!/usr/bin/env python3
"""Gera epg.xml só com os canais de tvpaga.m3u, usando os guias do epgshare01.
Casa canal e guia pelo nome normalizado e regrava o id do canal para o tvg-id da lista.
Também grava a linha url-tvg no cabeçalho do tvpaga.m3u."""
import gzip, html, io, re, sys, urllib.request

BASE = "https://epgshare01.online/epgshare01/epg_ripper_{}.xml.gz"
GUIAS = {"us": ["US2"], "uk": ["UK1"], "ca": ["CA2"], "au": ["AU1"], "ie": ["IE1"], "nz": ["NZ1"]}
ORDEM = ["us", "uk", "ca", "au", "ie", "nz"]          # busca em todos, começando pelo país do canal
EPG_URL = "https://raw.githubusercontent.com/ramalhou/lista-tv/main/epg.xml"

def norm(s):
    s = html.unescape(s).lower()
    s = re.sub(r"\((united states|united kingdom|canada|australia|ireland|new zealand|us|uk|ca)\)", "", s)
    s = re.sub(r"\([^)]*\)|\[[^]]*\]", "", s)
    s = s.replace("&", "and").replace("+", "plus")
    s = re.sub(r"\b(hd|sd|uhd|east|west|network|channel|tv|the)\b", "", s)
    return re.sub(r"[^a-z0-9]", "", s)

def baixar(codigo):
    req = urllib.request.Request(BASE.format(codigo), headers={"User-Agent": "Mozilla/5.0"})
    return gzip.decompress(urllib.request.urlopen(req, timeout=180).read()).decode("utf8", "ignore")

def main():
    guias = {}
    for pais in ORDEM:
        for cod in GUIAS[pais]:
            guias[pais] = baixar(cod)
    indice = {}
    for pais, xml in guias.items():
        m = {}
        for cid, corpo in re.findall(r'<channel id="([^"]*)">(.*?)</channel>', xml, re.S):
            for dn in re.findall(r"<display-name[^>]*>(.*?)</display-name>", corpo, re.S):
                m.setdefault(norm(dn), cid)
            m.setdefault(norm(html.unescape(cid).rsplit(".", 1)[0].replace(".", " ")), cid)
        indice[pais] = m

    linhas = open("tvpaga.m3u", encoding="utf8").read().splitlines()
    escolhidos = {}          # (pais_do_guia, id_no_guia) -> [tvg-id da lista, nome]
    for l in linhas:
        if not l.startswith("#EXTINF"):
            continue
        tid = re.search(r'tvg-id="([^"]*)"', l)
        nome = l.rsplit(",", 1)[1].strip()
        if not tid:
            continue
        pref = tid.group(1).split("@")[0].rsplit(".", 1)[-1]
        k = norm(nome)
        for pais in [pref] + [p for p in ORDEM if p != pref]:
            cid = indice.get(pais, {}).get(k)
            if k and cid:
                escolhidos.setdefault((pais, cid), []).append((tid.group(1), nome))
                break

    saida = ['<?xml version="1.0" encoding="UTF-8"?>', '<tv generator-info-name="lista-tv">']
    prog = []
    for (pais, cid), alvos in escolhidos.items():
        xml = guias[pais]
        for tvgid, nome in alvos:
            novo = html.escape(tvgid, quote=True)
            saida.append(f'<channel id="{novo}"><display-name>{html.escape(html.unescape(nome))}</display-name></channel>')
        cid_re = re.escape(cid)
        blocos = re.findall(r'<programme [^>]*channel="' + cid_re + r'".*?</programme>', xml, re.S)
        for tvgid, nome in alvos:
            novo = html.escape(tvgid, quote=True)
            for b in blocos:
                prog.append(re.sub(r'channel="[^"]*"', f'channel="{novo}"', b, count=1))
    saida += prog + ["</tv>"]
    open("epg.xml", "w", encoding="utf8").write("\n".join(saida) + "\n")

    if linhas and linhas[0].startswith("#EXTM3U"):
        linhas[0] = f'#EXTM3U url-tvg="{EPG_URL}"'
    open("tvpaga.m3u", "w", encoding="utf8").write("\n".join(linhas) + "\n")
    print(len(escolhidos), "guias casados;", len(prog), "programas")

if __name__ == "__main__":
    main()
