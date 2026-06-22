from agent.graph import graph

result = graph.invoke(
    {
        "query": "Latest AI news",
        "plan": "",
        "research": "",
        "answer": "",
        "need_search": False,
    }
)

print(result)