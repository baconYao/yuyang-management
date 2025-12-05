FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
RUN chmod +x /usr/local/bin/uv

WORKDIR /app

# Create a non-root user
RUN useradd -m -u 1000 appuser

# Copy dependency files first for better layer caching
COPY pyproject.toml .

# Create minimal app structure for editable install
RUN mkdir -p app && touch app/__init__.py

# Install dependencies (needs minimal app structure for -e .)
RUN uv pip install --system --no-cache -e .

# Copy application code
COPY app/ ./app/

# Change ownership to non-root user
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

