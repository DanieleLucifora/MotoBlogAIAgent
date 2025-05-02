import os
import json
import difflib
from datetime import datetime
from typing import TypedDict, Optional
from langgraph.graph import StateGraph
from langchain_openai import ChatOpenAI
from serpapi import GoogleSearch
from IPython.display import Image, display
from prompt import get_prompt_by_category

# File di storico per evitare ripetizioni di argomenti
HISTORY_FILE = "topic_history.json"

# Carica lo storico degli argomenti da file
def load_topic_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

# Salva lo storico aggiornato nel file JSON
def save_topic_history(history):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

# Controlla se un argomento è identico a uno già usato
def is_duplicate(new_topic, history):
    return any(new_topic.lower() == t["topic"].lower() for t in history)

# Controlla se un argomento è troppo simile ad altri passati
def is_similar(new_topic, history, threshold: float = 0.7):
    for old in history:
        ratio = difflib.SequenceMatcher(None, new_topic.lower(), old["topic"].lower()).ratio()
        if ratio >= threshold:
            return True
    return False

# Permette all'utente di scegliere la categoria del post
def select_topic_category() -> str:
    print("\nSeleziona una tipologia di post:")
    print("1 - Evento imminente")
    print("2 - Guida pratica")
    print("3 - Recensione prodotto")
    print("4 - Lascia scegliere all'agente (random)")
    choice = input("Inserisci il numero della tua scelta: ").strip()
    category_map = {
        "1": "upcoming_events",
        "2": "how_to",
        "3": "product_review",
        "4": "random"
    }
    return category_map.get(choice, "random")

# Definizione dello stato condiviso tra i nodi
class BlogState(TypedDict):
    topic: Optional[str]
    sources: Optional[list[str]]
    evaluations: Optional[list[str]]
    retry: Optional[bool]
    draft: Optional[str]

# Nodo 1: suggerisce un argomento originale, evitando duplicazioni
def suggest_topic(state: BlogState) -> BlogState:
    llm = ChatOpenAI(model="gpt-4.1-nano", temperature=0.8)
    selected_category = select_topic_category()
    history = load_topic_history()
    max_attempts = 5

    for _ in range(max_attempts):
        prompt = get_prompt_by_category(selected_category)
        response = llm.invoke(prompt)
        topic_suggestion = response.content.strip()

        if not is_duplicate(topic_suggestion, history) and not is_similar(topic_suggestion, history):
            history.append({
                "topic": topic_suggestion,
                "category": selected_category,
                "date": datetime.today().strftime("%Y-%m-%d")
            })
            save_topic_history(history)
            print(f"\n[Topic Suggester] Argomento suggerito: {topic_suggestion}")
            return {"topic": topic_suggestion, "sources": None, "evaluations": None, "retry": False, "draft": None}
        else:
            print(f"\n[Topic Suggester] Argomento duplicato o simile: {topic_suggestion}, ne genero un altro...")

    print("\nImpossibile trovare un argomento nuovo dopo diversi tentativi.")
    return {"topic": None, "sources": None, "evaluations": None, "retry": False, "draft": None}

# Nodo 2: ricerca fonti online e gestisce un eventuale retry
def retrieve_sources_web(state: BlogState) -> BlogState:
    topic = state["topic"]
    if not topic:
        print("\nNessun argomento generato. Il flusso viene interrotto.")
        exit(1)
    retry = state.get("retry", False)
    llm = ChatOpenAI(model="gpt-4.1-nano", temperature=0.3)

    if not retry:
        query = topic
    else:
        prompt = f'''
        L'argomento del post è: {topic}.
        Genera una query di ricerca Google più mirata per trovare contenuti di qualità pertinenti.
        '''
        response = llm.invoke(prompt)
        query = response.content.strip()

    print(f"\n[Source Retriever Web] Query per SerpAPI: {query}")

    search = GoogleSearch({
        "q": query,
        "location": "Italy",
        "hl": "it",
        "gl": "it",
        "api_key": os.environ.get("SERPAPI_API_KEY")
    })

    result = search.get_dict()
    organic_results = result.get("organic_results", [])

    sources = []
    for r in organic_results[:5]:
        title = r.get("title", "")
        snippet = r.get("snippet", "")
        link = r.get("link", "")
        sources.append(f"{title} - {snippet} ({link})")

    if not sources:
        print("\nNessuna fonte trovata.")
        return {"topic": topic, "sources": None, "evaluations": None, "retry": True, "draft": None}

    print("\n[Source Retriever Web] Fonti trovate:")
    for i, s in enumerate(sources, 1):
        print(f"  {i}. {s}")

    return {"topic": topic, "sources": sources, "evaluations": None, "retry": False, "draft": None}

# Nodo 3: valuta la qualità delle fonti recuperate
def evaluate_sources(state: BlogState) -> BlogState:
    topic = state["topic"]
    sources = state["sources"]
    llm = ChatOpenAI(model="gpt-4.1-nano", temperature=0.7)

    joined_sources = "\n".join(f"{i+1}. {s}" for i, s in enumerate(sources))
    prompt = f'''
    Stai aiutando un blogger a scegliere contenuti per un post su: "{topic}"
    Valuta 5 fonti su: RILEVANZA, AUTOREVOLEZZA, ATTUALITÀ, UTILITÀ pratica (1-10).
    Dai anche un punteggio totale e una breve spiegazione.
    {joined_sources}
    '''
    response = llm.invoke(prompt)
    evaluations = response.content.strip().split("\n")
    evaluations = [e.strip("-• ") for e in evaluations if e.strip()]

    print("\n[Source Evaluator] Valutazioni delle fonti:")
    for ev in evaluations:
        print(f"  - {ev}")

    return {"topic": topic, "sources": sources, "evaluations": evaluations, "retry": False, "draft": None}

# Nodo 4: genera una bozza di post basata su fonti ed analisi
def draft_post(state: BlogState) -> BlogState:
    topic = state["topic"]
    sources = state["sources"]
    evaluations = state["evaluations"]
    llm = ChatOpenAI(model="gpt-4.1-nano", temperature=0.7)

    source_text = "\n".join(sources)
    eval_text = "\n".join(evaluations)

    prompt = f'''
    Scrivi una bozza di post per un blog di viaggi in moto.
    Argomento: "{topic}"
    Fonti:
    {source_text}
    Valutazioni:
    {eval_text}
    Il post deve avere: introduzione, corpo, conclusione, essere utile e lungo max 300 parole.
    '''
    response = llm.invoke(prompt)
    draft = response.content.strip()

    print("\n[Post Drafter] Bozza generata:\n")
    print(draft)

    return {
        "topic": topic,
        "sources": sources,
        "evaluations": evaluations,
        "retry": False,
        "draft": draft
    }

# Costruzione del grafo agentico
builder = StateGraph(BlogState)
builder.add_node("topic_suggester", suggest_topic)
builder.add_node("source_retriever_web", retrieve_sources_web)
builder.add_node("source_evaluator", evaluate_sources)
builder.add_node("post_drafter", draft_post)

builder.set_entry_point("topic_suggester")
builder.add_edge("topic_suggester", "source_retriever_web")
builder.add_conditional_edges(
    "source_retriever_web",
    lambda state: "source_retriever_web" if state.get("retry") else "source_evaluator"
)
builder.add_edge("source_evaluator", "post_drafter")
builder.set_finish_point("post_drafter")

# Compila e salva il grafo come immagine
graph = builder.compile()
with open("graph.png", "wb") as f:
    f.write(graph.get_graph().draw_mermaid_png())

# Stato iniziale per avviare il processo
initial_state: BlogState = {
    "topic": None,
    "sources": None,
    "evaluations": None,
    "retry": False,
    "draft": None
}

# Invocazione finale del grafo
final_state = graph.invoke(initial_state)
