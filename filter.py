#!/usr/bin/env python3
"""Filtra a lista iptv-org (inglês) e deixa só canais com perfil de TV paga.
Regras ajustáveis no topo. Saída: tvpaga.m3u"""
import re, sys, urllib.request

SRC = "https://iptv-org.github.io/iptv/languages/eng.m3u"
PAISES = {"us", "uk", "ca", "au", "nz", "ie"}        # países aceitos (sufixo do tvg-id)
IDIOMAS_OK = {"eng", "por"}                           # o 1o idioma do feed (iptv-org) tem de ser um destes
IDIOMAS_FORA = {"hin", "pan", "tha", "ind", "ara", "urd", "tur", "rus"}  # feeds que misturam estes idiomas saem
FEEDS = "https://iptv-org.github.io/api/feeds.json"
RES_MIN = 720                                         # resolução mínima quando informada no nome
CATEGORIAS_FORA = {"Religious", "Legislative", "Shop"}
# Marcas/canais com perfil de TV paga. Só entra quem casar com esta lista.
MARCAS = re.compile(r"\b(hbo|cinemax|showtime|starz|epix|mgm\+|amc|fx|fxx|fxm|ifc|sundance|tcm|"
    r"turner classic|tnt|tbs|trutv|cnn|hln|cnbc|msnbc|msnow|bloomberg|fox news|fox business|"
    r"fox sports|espn|nbc sports|golf channel|nfl|nba|nhl|mlb|sky sports|tnt sports|bt sport|"
    r"eurosport|discovery|animal planet|tlc|investigation discovery|id\b|hgtv|food network|"
    r"travel channel|cooking channel|diy|nat ?geo|national geographic|history|h2|military history|"
    r"a&e|a\+e|lifetime|oxygen|bravo|e!|syfy|usa network|paramount|comedy central|mtv|vh1|cmt|"
    r"bet\b|nickelodeon|nick jr|nicktoons|cartoon network|boomerang|disney|hallmark|"
    r"ovation|reelz|smithsonian|science channel|bbc|itv|channel 4|channel 5|sky |dave|"
    r"gold\b|alibi|yesterday|drama\b|w channel|e4|film4|more4|comedy|crime \+|"
    r"al jazeera|dw\b|france 24|euronews|cbs|nbc\b|abc\b|fox\b|cw\b|pbs|"
    r"ctv|cbc|global tv|citytv|ion\b|laff|grit|bounce|court tv|newsmax|newsnation)",re.I)
# Estações locais (ABC KAAL, CBS WJAX-TV...), variantes repetidas e canais FAST de marca de plataforma
LOCAL = re.compile(r"^(abc|cbs|nbc|fox|cw|pbs|ctv|cbc|citytv)\s+[kw][a-z]{2,3}(-[a-z]{2})?\b|"
                   r"\([a-z ]+\)\s+[kw][a-z]{2,3}(-[a-z]{2})?\s*(\(|$)|^[kw][a-z]{2,3}-tv|mrvtv|puto tv|radio|live \d+|live event|pluto|roku|samsung|stirr|xumo|tubi|lakewood|\bnews (baltimore|boston|chicago|colorado|detroit|miami|minnesota|philly|pittsburgh|sacramento|bay area)", re.I)
NOME_FORA = re.compile(r"geo-blocked|not 24/7|public access|council|parliament|committee|"
                       r"hearing room|city of|county|school|university|church|"
                       r"espa[nñ]ol|latin america|latino|deportes|turkiye|romania|hungary|czech", re.I)

def attr(l, k):
    m = re.search(k + r'="([^"]*)"', l)
    return m.group(1) if m else ""

def carregar_idiomas():
    import json
    dados = json.loads(urllib.request.urlopen(FEEDS, timeout=120).read().decode("utf8"))
    return {(e["channel"], e["id"]): e.get("languages") or [] for e in dados}

def idioma_ok(tid, idiomas):
    canal, _, feed = tid.partition("@")
    langs = idiomas.get((canal, feed))
    if not langs:
        return True            # sem informação: não corta
    return langs[0] in IDIOMAS_OK and not (set(langs) & IDIOMAS_FORA)

def main():
    idiomas = carregar_idiomas()
    txt = urllib.request.urlopen(SRC, timeout=60).read().decode("utf8")
    linhas = txt.splitlines()
    out, i = ["#EXTM3U"], 0
    while i < len(linhas):
        if linhas[i].startswith("#EXTINF"):
            j = i + 1
            extra = []
            while j < len(linhas) and linhas[j].startswith("#"):
                extra.append(linhas[j]); j += 1
            url = linhas[j] if j < len(linhas) else ""
            inf = linhas[i]
            nome = inf.rsplit(",", 1)[1]
            tid = attr(inf, "tvg-id")
            pais = tid.split("@")[0].rsplit(".", 1)[-1] if "." in tid else ""
            cats = set(attr(inf, "group-title").split(";"))
            m = re.search(r"\((\d{3,4})p\)", nome)
            res = int(m.group(1)) if m else None
            ok = (pais in PAISES and MARCAS.search(nome) and not LOCAL.search(nome)
                  and not (cats & CATEGORIAS_FORA)
                  and not NOME_FORA.search(nome) and (res is None or res >= RES_MIN)
                  and idioma_ok(tid, idiomas))
            if ok:
                out += [inf] + extra + [url]
            i = j
        i += 1
    open("tvpaga.m3u", "w", encoding="utf8").write("\n".join(out) + "\n")
    print(sum(1 for x in out if x.startswith("#EXTINF")), "canais")

if __name__ == "__main__":
    main()
