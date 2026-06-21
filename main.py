from agent.graph import graph

result = graph.invoke(
    {
        "message": "Hello Agent"
    }
)

print(result)