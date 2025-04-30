import random
import datetime

def get_today() -> str:
    return datetime.datetime.today().strftime("%A %d %B %Y")  

def prompt_upcoming_events() -> str:
    today = get_today()
    return f"""
Sei un esperto di moto e viaggi in moto. Oggi è {today}.
Proponi un titolo accattivante (max 10 parole) per un post su un evento motociclistico italiano che si terrà **nei prossimi 3 mesi**.

Requisiti:
- L’evento può essere reale o verosimile
- Non considerare eventi che abbiano a che fare con il ciclismo, considera solo eventi per moto e motociclismo
- Preferisci novità, piccoli raduni locali o fiere stagionali
"""

def prompt_how_to() -> str:
    today = get_today()
    return f"""
Sei un esperto di moto e viaggi in moto. Oggi è {today}.
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
Sei un esperto di moto e viaggi in moto. Oggi è {today}.
Proponi un titolo per un post che recensisca un prodotto innovativo utile durante i viaggi in moto.

Il titolo deve:
- indicare chiaramente il prodotto (marca e modello)
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