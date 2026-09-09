import io

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def generate_chart(columns: list[str], rows: list[tuple], chart_type: str, title: str) -> bytes:
    labels = [str(row[0]) for row in rows]
    values = [row[1] for row in rows]

    fig, ax = plt.subplots(figsize=(8, 5))

    if chart_type == "bar":
        ax.bar(labels, values)
        plt.setp(ax.get_xticklabels(), rotation=45, ha="right")
    elif chart_type == "line":
        ax.plot(labels, values, marker="o")
        plt.setp(ax.get_xticklabels(), rotation=45, ha="right")
    else:
        raise ValueError(f"Type de graphique non supporté : {chart_type}")

    ax.set_xlabel(columns[0])
    ax.set_ylabel(columns[1])
    ax.set_title(title)
    fig.tight_layout()

    buffer = io.BytesIO()
    fig.savefig(buffer, format="png")
    plt.close(fig)
    buffer.seek(0)

    return buffer.getvalue()