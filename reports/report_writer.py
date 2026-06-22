import os
from datetime import datetime


def save_report(content):

    os.makedirs(
        "reports",
        exist_ok=True
    )

    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    filename = (
        f"reports/report_{timestamp}.md"
    )

    with open(
        filename,
        "w",
        encoding="utf-8"
    ) as file:

        file.write(content)

    return filename