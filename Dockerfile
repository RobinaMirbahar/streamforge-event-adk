FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY multilora_adk_eval/ ./multilora_adk_eval/
COPY scripts/ ./scripts/
ENV PORT=8080
EXPOSE 8080
CMD ["python", "scripts/run_multilora_adk_eval.py"]
