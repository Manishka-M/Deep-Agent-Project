from typing import TypedDict


class AgentState(TypedDict):
    query: str
    plan: str
    research: str
    answer: str
    need_search: bool