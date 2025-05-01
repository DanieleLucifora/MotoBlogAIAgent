import os
import datetime
from serpapi import GoogleSearch
from themes import get_random_theme
from typing import Callable

def get_today() -> str:
    return datetime.datetime.today().strftime("%A %d %B %Y")

def prompt_upcoming_events() -> str:
    today = get_today()
    params = {
        "q": "eventi motociclistici in Italia nei prossimi 6 mesi",
        "location": "Italy",
        "hl": "it",
        "gl": "it",
        "api_key": os.getenv("SERPAPI_API_KEY")
    }
    search = GoogleSearch(params)
    result = search.get_dict()
    organic_results = result.get("organic_results", [])

    search_results = ""
    for r in organic_results[:5]:
        title = r.get("title", "")
        snippet = r.get("snippet", "")
        link = r.get("link", "")
        search_results += f"- {title}: {snippet} ({link})\n"

    return f"""
Oggi è {today}. Sei un esperto di viaggi in moto.

Ecco una lista di eventi motociclistici reali trovati online:

{search_results}

Scegli **uno di questi eventi** e proponi un titolo per la creazione di un post.

Requisiti:
- Il titolo deve riferirsi a un **evento reale** tra quelli sopra
- **Escludi eventi legati al ciclismo o altre categorie**
- Deve ispirare **curiosità** o senso di **comunità tra motociclisti**
- Scrivilo in **massimo 10 parole**, **una sola riga**, **senza virgolette**
"""

def prompt_how_to() -> str:
    today = get_today()
    theme = get_random_theme("how_to")
    return f"""
Oggi è {today}. Sei un motociclista esperto di lunghi viaggi.

Aiuta un blogger a scrivere un post-guida pratico.
Proponi un titolo originale che inizi con "Come...", incentrato sul tema: **{theme}**.

Requisiti:
- Deve essere **pratico e specifico**, non astratto o ripetitivo
- Massimo 10 parole, una riga, senza virgolette
"""

def prompt_product_review() -> str:
    today = get_today()
    theme = get_random_theme("product_review")
    return f"""
Oggi è {today}. Sei un esperto di accessori per moto e tecnologia da viaggio.

Stai aiutando un blogger a scrivere un post di recensione.
Scegli un **prodotto innovativo** di tipo: **{theme}**, e proponi un **titolo coinvolgente** per recensirlo.

Requisiti:
- Indica **marca e modello** del prodotto
- Il titolo deve contenere una **promessa o domanda stimolante**
  Esempi: “Vale davvero il prezzo?” – “Il compagno perfetto per l’avventura?”
- Scrivilo in **massimo 10 parole**, **una sola riga**, **senza virgolette**
- Usa un tono **promozionale ma realistico**
"""

def get_prompt_by_category(choice: str) -> str:
    prompts: dict[str, Callable[[], str]] = {
        "upcoming_events": prompt_upcoming_events,
        "how_to": prompt_how_to,
        "product_review": prompt_product_review,
    }
    import random
    return prompts.get(choice, random.choice(list(prompts.values())))()