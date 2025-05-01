import random

HOW_TO_THEMES = [
    "equipaggiamento", "meteo", "salute del motociclista",
    "navigazione offline", "sicurezza in strada", "carico bagagli",
    "manutenzione essenziale", "comunicazione in viaggio", "organizzazione e pianificazione viaggio",
    "problemi con pioggia e umidità", "rifornimenti e carburante", "gestione della stanchezza",
    "risparmio spazio", "controlli prima della partenza"
]

PRODUCT_REVIEW_THEMES = [
    "navigatore GPS", "borsa da serbatoio", "giacca tecnica", "app per itinerari moto",
    "interfono bluetooth", "supporto smartphone da manubrio", "tenda da viaggio per motociclisti",
    "action cam per casco", "guanti riscaldati", "sella ergonomica", "valigie moto",
    "parabrezza regolabile", "abbigliamento impermeabile", "kit di pronto soccorso per moto"
]

def get_random_theme(category: str) -> str:
    if category == "how_to":
        return random.choice(HOW_TO_THEMES)
    elif category == "product_review":
        return random.choice(PRODUCT_REVIEW_THEMES)
    else:
        return ""