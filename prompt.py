import random
import datetime

def get_today() -> str:
    return datetime.datetime.today().strftime("%A %d %B %Y")  # es. Martedì 30 Aprile 2025

def prompt_upcoming_events() -> str:
    today = get_today()
    return f"""
Sei un blogger esperto di viaggi in moto. Oggi è {today}.
Scrivi un argomento per un post che segnali un evento motociclistico imminente in Italia (raduni, fiere, incontri su due ruote).

Il titolo del post deve:
- essere coerente con la data odierna
- fare riferimento a un evento plausibile o reale
- interessare i motociclisti in viaggio o in pianificazione
- essere scritto in massimo 10 parole
"""

def prompt_how_to() -> str:
    today = get_today()
    return f"""
Sei un blogger appassionato di viaggi in moto. Oggi è {today}.
Proponi un argomento per un post guida “how to”.

Il titolo deve:
- iniziare con 'Come...'
- risolvere un problema concreto
- essere utile per motociclisti in viaggio
- essere originale e non banale
- essere scritto in massimo 10 parole
"""

def prompt_product_review() -> str:
    today = get_today()
    return f"""
Sei un blogger che recensisce prodotti per motociclisti. Oggi è {today}.
Suggerisci un titolo per un post che recensisca un prodotto innovativo utile durante i viaggi in moto.

Il titolo deve:
- indicare chiaramente il prodotto (marca e modello)
- evitare prodotti già noti o troppo comuni (es. GPS)
- incuriosire il lettore con una domanda o una promessa
- essere breve (max 10 parole)
"""

def get_prompt_by_category(choice: str) -> str:
    prompts = {
        "upcoming_events": prompt_upcoming_events,
        "how_to": prompt_how_to,
        "product_review": prompt_product_review,
    }
    return prompts.get(choice, random.choice(list(prompts.values())))()