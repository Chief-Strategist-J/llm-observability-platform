FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r /app/requirements.txt
COPY app/ /app/app/
COPY core/ /app/core/
COPY .env.llm_chat_app /app/.env
ENV PYTHONPATH="/app"
EXPOSE 8501
CMD ["streamlit", "run", "app/main.py", "--server.port=8501", "--server.address=0.0.0.0"]
