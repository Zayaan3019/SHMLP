FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml requirements.txt README.md /app/
RUN pip install --no-cache-dir -r requirements.txt

COPY src /app/src

ENV PYTHONPATH=/app/src

CMD ["python", "-m", "shmlrp", "api", "--host", "0.0.0.0", "--port", "8000"]
