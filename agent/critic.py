from agent.llm import llm


def critique_report(report: str):

    prompt = f"""
You are a research quality reviewer.

Review the report below.

Determine:

1. Is the report complete?
2. Are important topics missing?
3. Does more research need to be done?

Answer ONLY in this format:

VERDICT: YES

or

VERDICT: NO

Then explain briefly.

Report:
{report}
"""

    response = llm.invoke(prompt)

    return response.content