import json
import os
from typing import Any, TypedDict

from dotenv import load_dotenv
from openai import OpenAI
from langgraph.graph import END, StateGraph

from schemas import IncidentAnalysis
from rag import retrieve_relevant_sops
from tools import get_equipment_history, search_maintenance_logs


load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY is missing in .env")

client = OpenAI(api_key=OPENAI_API_KEY)


class AgentState(TypedDict):
    issue: str
    asset_id: str
    sop_results: list[dict[str, Any]]
    log_results: list[dict[str, Any]]
    equipment_history: dict[str, Any]
    final_answer: dict[str, Any]


def planner_node(state: AgentState) -> AgentState:
    return state


def retrieve_sops_node(state: AgentState) -> AgentState:
    state["sop_results"] = retrieve_relevant_sops(state["issue"])
    return state


def retrieve_logs_node(state: AgentState) -> AgentState:
    state["log_results"] = search_maintenance_logs(state["issue"], state["asset_id"])
    return state


def equipment_history_node(state: AgentState) -> AgentState:
    state["equipment_history"] = get_equipment_history(state["asset_id"])
    return state


def _build_prompt(state: AgentState) -> str:
    return f"""
You are an LNG operations incident analysis assistant.

Your job is to analyze an equipment issue using ONLY the retrieved evidence below.
Do not invent facts. Keep recommendations practical and operations-focused.

User issue:
{state["issue"]}

Asset ID:
{state["asset_id"]}

Retrieved SOPs:
{json.dumps(state["sop_results"], indent=2)}

Retrieved maintenance logs:
{json.dumps(state["log_results"], indent=2)}

Equipment history:
{json.dumps(state["equipment_history"], indent=2)}

Return ONLY valid JSON with this exact schema:
{{
  "summary": "string",
  "possible_causes": ["string"],
  "recommended_checks": ["string"],
  "confidence": "Low or Medium or High",
  "tools_used": ["search_sops", "search_maintenance_logs", "get_equipment_history"],
  "sources": ["string"]
}}

Rules:
- Use only evidence from the provided context.
- recommended_checks should be short, practical, and operator-friendly.
- confidence should reflect how much evidence exists.
- sources must reference the retrieved SOP/log source names or equipment_history.json.
""".strip()


def synthesis_node(state: AgentState) -> AgentState:
    prompt = _build_prompt(state)

    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        temperature=0,
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a reliable enterprise AI assistant that must return strict JSON only."
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
    )

    content = response.choices[0].message.content
    if not content:
        raise ValueError("OpenAI returned an empty response.")

    parsed = json.loads(content)

    parsed.setdefault("summary", "No summary generated.")
    parsed.setdefault("possible_causes", [])
    parsed.setdefault("recommended_checks", [])
    parsed.setdefault("confidence", "Medium")
    parsed.setdefault(
        "tools_used",
        ["search_sops", "search_maintenance_logs", "get_equipment_history"],
    )

    if "sources" not in parsed or not parsed["sources"]:
        sources: list[str] = []
        sources.extend([item["source"] for item in state["sop_results"] if "source" in item])
        sources.extend([item["source"] for item in state["log_results"] if "source" in item])
        if state["equipment_history"]:
            sources.append("equipment_history.json")
        parsed["sources"] = list(dict.fromkeys(sources))

    validated = IncidentAnalysis(**parsed)
    state["final_answer"] = validated.model_dump()
    return state


def build_graph():
    graph = StateGraph(AgentState)

    graph.add_node("planner", planner_node)
    graph.add_node("retrieve_sops", retrieve_sops_node)
    graph.add_node("retrieve_logs", retrieve_logs_node)

    # Renamed node to avoid conflict with state key "equipment_history"
    graph.add_node("fetch_equipment_history", equipment_history_node)

    graph.add_node("synthesis", synthesis_node)

    graph.set_entry_point("planner")
    graph.add_edge("planner", "retrieve_sops")
    graph.add_edge("retrieve_sops", "retrieve_logs")
    graph.add_edge("retrieve_logs", "fetch_equipment_history")
    graph.add_edge("fetch_equipment_history", "synthesis")
    graph.add_edge("synthesis", END)

    return graph.compile()


agent_graph = build_graph()


def run_agent(issue: str, asset_id: str) -> dict[str, Any]:
    initial_state: AgentState = {
        "issue": issue,
        "asset_id": asset_id,
        "sop_results": [],
        "log_results": [],
        "equipment_history": {},
        "final_answer": {},
    }

    result = agent_graph.invoke(initial_state)
    return result["final_answer"]