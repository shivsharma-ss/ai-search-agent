"""Research pipeline orchestration using LangGraph.

This module wires together search (Google, Bing, Reddit), post retrieval,
LLM-based analysis for each source, and final synthesis into a single
callable function for API and CLI usage.
"""

from typing import Annotated, Dict, List, Optional, TypedDict

import os
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from pydantic import BaseModel, Field

from .prompts import (
    get_bing_analysis_messages,
    get_google_analysis_messages,
    get_reddit_analysis_messages,
    get_reddit_url_analysis_messages,
    get_synthesis_messages,
)
from .web_operations import reddit_post_retrieval, reddit_search_api, serp_search

load_dotenv()


def _init_llm(openai_api_key: str | None = None):
    """Initialize chat model, optionally using a provided API key."""
    if openai_api_key:
        os.environ["OPENAI_API_KEY"] = openai_api_key
    return init_chat_model("gpt-4o")


class State(TypedDict):
    messages: Annotated[list, add_messages]
    user_question: Optional[str]
    google_results: Optional[str]
    bing_results: Optional[str]
    reddit_results: Optional[str]
    selected_reddit_urls: Optional[List[str]]
    reddit_post_data: Optional[list]
    google_analysis: Optional[str]
    bing_analysis: Optional[str]
    reddit_analysis: Optional[str]
    final_answer: Optional[str]
    # Runtime config
    config: Optional[dict]
    # LLM instance to use
    llm: Optional[object]


class RedditURLAnalysis(BaseModel):
    """Structured output for extracting Reddit URLs to deep dive into."""

    selected_urls: List[str] = Field(
        description=(
            "List of Reddit URLs that contain valuable information for answering "
            "the user's question"
        )
    )


def google_search(state: State):
    user_question = state.get("user_question", "") or ""
    print(f"🔎 Google: searching for → {user_question}")
    cfg = state.get("config") or {}
    google_results = serp_search(
        user_question, engine="google", api_key=cfg.get("brightdata_api_key")
    )
    try:
        n = len((google_results or {}).get("organic", []))
        print(f"✅ Google: got {n} organic results")
    except Exception:
        print("✅ Google: search completed")
    return {"google_results": google_results}


def bing_search(state: State):
    user_question = state.get("user_question", "") or ""
    print(f"🔎 Bing: searching for → {user_question}")
    cfg = state.get("config") or {}
    bing_results = serp_search(
        user_question, engine="bing", api_key=cfg.get("brightdata_api_key")
    )
    try:
        n = len((bing_results or {}).get("organic", []))
        print(f"✅ Bing: got {n} organic results")
    except Exception:
        print("✅ Bing: search completed")
    return {"bing_results": bing_results}


def reddit_search(state: State):
    user_question = state.get("user_question", "") or ""
    print(f"🔎 Reddit: searching for → {user_question}")
    cfg = state.get("config") or {}
    reddit_results = reddit_search_api(
        keyword=user_question,
        api_key=cfg.get("brightdata_api_key"),
        dataset_id=cfg.get("reddit_dataset_id"),
    )
    try:
        total = (reddit_results or {}).get("total_found", 0)
        print(f"✅ Reddit: found {total} posts")
    except Exception:
        print("✅ Reddit: search completed")
    return {"reddit_results": reddit_results}


def analyze_reddit_posts(state: State):
    user_question = state.get("user_question", "") or ""
    reddit_results = state.get("reddit_results")
    if not reddit_results:
        return {"selected_reddit_urls": []}
    llm = state.get("llm")
    structured_llm = llm.with_structured_output(RedditURLAnalysis)
    messages = get_reddit_url_analysis_messages(user_question, reddit_results)

    try:
        analysis = structured_llm.invoke(messages)
        selected_urls = analysis.selected_urls
        print("🔗 Selected Reddit URLs:")
        for i, url in enumerate(selected_urls, 1):
            print(f"   {i}. {url}")
    except Exception as e:
        print(e)
        selected_urls = []

    return {"selected_reddit_urls": selected_urls}


def retrieve_reddit_posts(state: State):
    print("🧵 Retrieving Reddit post comments…")
    selected_urls = state.get("selected_reddit_urls", []) or []
    if not selected_urls:
        return {"reddit_post_data": []}

    print(f"📥 Processing {len(selected_urls)} Reddit URLs")
    cfg = state.get("config") or {}
    reddit_post_data = reddit_post_retrieval(
        selected_urls,
        api_key=cfg.get("brightdata_api_key"),
        comments_dataset_id=cfg.get("reddit_comments_dataset_id"),
    )
    if reddit_post_data:
        print(f"✅ Retrieved {len(reddit_post_data)} posts")
    else:
        print("❌ Failed to get post data")
        reddit_post_data = []

    return {"reddit_post_data": reddit_post_data}


def analyze_google_results(state: State):
    print("🧠 Analyzing Google results…")
    user_question = state.get("user_question", "") or ""
    google_results = state.get("google_results", "")
    messages = get_google_analysis_messages(user_question, google_results)
    llm = state.get("llm")
    reply = llm.invoke(messages)  # type: ignore[attr-defined]
    return {"google_analysis": reply.content}


def analyze_bing_results(state: State):
    print("🧠 Analyzing Bing results…")
    user_question = state.get("user_question", "") or ""
    bing_results = state.get("bing_results", "")
    messages = get_bing_analysis_messages(user_question, bing_results)
    llm = state.get("llm")
    reply = llm.invoke(messages)  # type: ignore[attr-defined]
    return {"bing_analysis": reply.content}


def analyze_reddit_results(state: State):
    print("🧠 Analyzing Reddit results…")
    user_question = state.get("user_question", "") or ""
    reddit_results = state.get("reddit_results", "")
    reddit_post_data = state.get("reddit_post_data", "")
    messages = get_reddit_analysis_messages(
        user_question, reddit_results, reddit_post_data
    )
    llm = state.get("llm")
    reply = llm.invoke(messages)  # type: ignore[attr-defined]
    return {"reddit_analysis": reply.content}


def synthesize_analyses(state: State):
    print("🧪 Synthesizing analyses into a final answer…")
    user_question = state.get("user_question", "") or ""
    google_analysis = state.get("google_analysis", "")
    bing_analysis = state.get("bing_analysis", "")
    reddit_analysis = state.get("reddit_analysis", "")
    messages = get_synthesis_messages(
        user_question, google_analysis, bing_analysis, reddit_analysis
    )
    llm = state.get("llm")
    reply = llm.invoke(messages)  # type: ignore[attr-defined]
    final_answer = reply.content
    print("🏁 Synthesis complete.")
    return {
        "final_answer": final_answer,
        "messages": [{"role": "assistant", "content": final_answer}],
    }


def build_graph() -> StateGraph:
    """Build and compile the LangGraph state machine for the pipeline."""
    graph_builder = StateGraph(State)
    graph_builder.add_node("google_search", google_search)
    graph_builder.add_node("bing_search", bing_search)
    graph_builder.add_node("reddit_search", reddit_search)
    graph_builder.add_node("analyze_reddit_posts", analyze_reddit_posts)
    graph_builder.add_node("retrieve_reddit_posts", retrieve_reddit_posts)
    graph_builder.add_node("analyze_google_results", analyze_google_results)
    graph_builder.add_node("analyze_bing_results", analyze_bing_results)
    graph_builder.add_node("analyze_reddit_results", analyze_reddit_results)
    graph_builder.add_node("synthesize_analyses", synthesize_analyses)

    graph_builder.add_edge(START, "google_search")
    graph_builder.add_edge(START, "bing_search")
    graph_builder.add_edge(START, "reddit_search")

    graph_builder.add_edge("google_search", "analyze_reddit_posts")
    graph_builder.add_edge("bing_search", "analyze_reddit_posts")
    graph_builder.add_edge("reddit_search", "analyze_reddit_posts")
    graph_builder.add_edge("analyze_reddit_posts", "retrieve_reddit_posts")

    graph_builder.add_edge("retrieve_reddit_posts", "analyze_google_results")
    graph_builder.add_edge("retrieve_reddit_posts", "analyze_bing_results")
    graph_builder.add_edge("retrieve_reddit_posts", "analyze_reddit_results")

    graph_builder.add_edge("analyze_google_results", "synthesize_analyses")
    graph_builder.add_edge("analyze_bing_results", "synthesize_analyses")
    graph_builder.add_edge("analyze_reddit_results", "synthesize_analyses")

    graph_builder.add_edge("synthesize_analyses", END)
    return graph_builder.compile()


# Compile once at import time for reuse.
graph = build_graph()


def run_research(
    question: str,
    config: Optional[dict] = None,
    *,
    openai_api_key: str | None = None,
    llm_override: object | None = None,
) -> Dict[str, object]:
    """Run the full research pipeline and return results.

    Args:
        question: User question to research.

    Returns:
        Dict containing final answer and intermediate artifacts.
    """
    print(f"\n🚀 Starting research for: {question}")
    llm = llm_override or _init_llm(openai_api_key)

    init_state: State = {
        "messages": [{"role": "user", "content": question}],
        "user_question": question,
        "google_results": None,
        "bing_results": None,
        "reddit_results": None,
        "selected_reddit_urls": None,
        "reddit_post_data": None,
        "google_analysis": None,
        "bing_analysis": None,
        "reddit_analysis": None,
        "final_answer": None,
        "config": config or {},
        "llm": llm,
    }

    final_state = graph.invoke(init_state)
    print("✨ Research pipeline finished.\n")
    return final_state
