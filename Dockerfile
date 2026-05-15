FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

WORKDIR /app

COPY pyproject.toml uv.lock README.md ./
COPY src ./src
COPY app.py ./
COPY data ./data
COPY .streamlit ./.streamlit

RUN uv sync --frozen --no-dev --python 3.12 --link-mode copy

ENV PATH="/app/.venv/bin:${PATH}"
ENV MLFQ_DATA_DIR="/app/data"

EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.address", "0.0.0.0", "--server.port", "8501"]
