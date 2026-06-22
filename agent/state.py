from typing import TypedDict, List, Dict


class AgentState(TypedDict):
    query: str

    plan: str

    todos: List[Dict]

    notes: List[Dict]

    research: str

    answer: str

    critique: str