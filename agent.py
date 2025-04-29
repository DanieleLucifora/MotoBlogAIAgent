import os
import json
from typing import TypedDict, Optional
from langgraph.graph import StateGraph
from langchain_openai import ChatOpenAI
from serpapi import GoogleSearch

from prompt import get_prompt_by_category

# === Costanti ===
HISTORY_FILE = "topic_history.json"

# === Funzioni di gestione dello storico ===
def load_topic_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_topic_history(history):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

def is_duplicate(topic, history):
    return topic.lower() in (t.lower() for t in history)

def select_topic_category() -> str:
    print("\n📌 Seleziona una tipologia di post:")
    print("1 - Evento imminente")
    print("2 - Guida pratica")
    print("3 - Recensione prodotto")
    print("4 - Lascia scegliere all'agente (random)")

    choice = input("👉 Inserisci il numero della tua scelta: ").strip()

    category_map = {
        "1": "upcoming_events",
        "2": "how_to",
        "3": "product_review",
        "4": "random"
    }

    return category_map.get(choice, "random")

# Stato del sistema
class BlogState(TypedDict):
    topic: Optional[str]
    sources: Optional[list[str]]
    evaluations: Optional[list[str]]
    retry: Optional[bool]  # Indica se si è già provato il fallback
    draft: Optional[str]

# Nodo: Topic Suggester
def suggest_topic(state: BlogState) -> BlogState:
    llm = ChatOpenAI(model="gpt-4o", temperature=0.8)
    selected_category = select_topic_category()
    prompt = get_prompt_by_category(selected_category)

    history = load_topic_history()
    max_attempts = 5

    for _ in range(max_attempts):
        response = llm.invoke(prompt)
        topic_suggestion = response.content.strip()
        if not is_duplicate(topic_suggestion, history):
            history.append(topic_suggestion)
            save_topic_history(history)
            print(f"\n[Topic Suggester] Argomento suggerito: {topic_suggestion}")
            return {"topic": topic_suggestion, "sources": None, "evaluations": None, "retry": False, "draft": None}
        else:
            print(f"\n[Topic Suggester] Argomento duplicato: {topic_suggestion}, ne genero un altro...")

    print("\n⚠️ Impossibile trovare un argomento nuovo dopo diversi tentativi.")
    return {"topic": None, "sources": None, "evaluations": None, "retry": False, "draft": None}

# Nodo: Source Retriever Web con fallback e ricerca mirata
def retrieve_sources_web(state: BlogState) -> BlogState:
    topic = state["topic"]
    retry = state.get("retry", False)
    llm = ChatOpenAI(model="gpt-4o", temperature=0.3)

    if not retry:
        query = topic
    else:
        prompt = f"""
        L'argomento del post è: {topic}.
        Genera una query di ricerca Google più mirata per trovare contenuti di qualità pertinenti a questo argomento.
        La query deve essere in italiano e orientata a contenuti pratici.
        """
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
        print("\n⚠️ Nessuna fonte trovata.")
        return {"topic": topic, "sources": None, "evaluations": None, "retry": True, "draft": None}

    print("\n[Source Retriever Web] Fonti trovate:")
    for i, s in enumerate(sources, 1):
        print(f"  {i}. {s}")

    return {"topic": topic, "sources": sources, "evaluations": None, "retry": False, "draft": None}

# Nodo: Source Evaluator
def evaluate_sources(state: BlogState) -> BlogState:
    topic = state["topic"]
    sources = state["sources"]
    llm = ChatOpenAI(model="gpt-4", temperature=0.7)

    joined_sources = "\n".join(f"{i+1}. {s}" for i, s in enumerate(sources))
    prompt = f"""
    Stai aiutando un blogger a scegliere contenuti per un post su:
    "{topic}"

    Qui ci sono 5 fonti trovate online:
    {joined_sources}

    Valuta ciascuna fonte da 1 a 10 (1 = poco utile o inaffidabile, 10 = molto utile e pertinente), 
    spiegando brevemente il motivo. Rispondi in elenco numerato.
    """
    response = llm.invoke(prompt)
    evaluations = response.content.strip().split("\n")
    evaluations = [e.strip("-• ") for e in evaluations if e.strip()]

    print("\n[Source Evaluator] Valutazioni delle fonti:")
    for ev in evaluations:
        print(f"  - {ev}")

    return {"topic": topic, "sources": sources, "evaluations": evaluations, "retry": False, "draft": None}

# Nodo: Post Drafter
def draft_post(state: BlogState) -> BlogState:
    topic = state["topic"]
    sources = state["sources"]
    evaluations = state["evaluations"]
    llm = ChatOpenAI(model="gpt-4", temperature=0.7)

    source_text = "\n".join(sources)
    eval_text = "\n".join(evaluations)

    prompt = f"""
    Scrivi una bozza di post per un blog di viaggi in moto.

    Argomento: "{topic}"

    Fonti da considerare:
    {source_text}

    Valutazioni di qualità delle fonti:
    {eval_text}

    Il post deve:
    - essere utile, concreto e amichevole
    - avere un'introduzione, corpo e conclusione
    - includere consigli pratici
    - essere lungo massimo 300 parole
    """

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

# Costruzione del grafo
builder = StateGraph(BlogState)
builder.add_node("topic_suggester", suggest_topic)
builder.add_node("source_retriever_web", retrieve_sources_web)
builder.add_node("source_evaluator", evaluate_sources)
builder.add_node("post_drafter", draft_post)

# Routing condizionale
builder.set_entry_point("topic_suggester")
builder.add_edge("topic_suggester", "source_retriever_web")
builder.add_conditional_edges(
    "source_retriever_web",
    lambda state: "source_retriever_web" if state.get("retry") else "source_evaluator"
)
builder.add_edge("source_evaluator", "post_drafter")
builder.set_finish_point("post_drafter")

graph = builder.compile()

# Esecuzione
initial_state: BlogState = {"topic": None, "sources": None, "evaluations": None, "retry": False, "draft": None}
final_state = graph.invoke(initial_state)
