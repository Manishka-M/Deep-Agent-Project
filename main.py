from agent.graph import graph
result = graph.invoke(
    {
        "query": "Generate a report on AI in Healthcare",
        "plan": "",
        "todos": [],
        "notes": [],
        "research": "",
        "answer": "",
        "critique": ""
    }
)

print(result)