from agent.memory import save_notes
from agent.memory import load_notes


save_notes(
    [
        {
            "task": "test",
            "content": "hello"
        }
    ]
)

print(load_notes())