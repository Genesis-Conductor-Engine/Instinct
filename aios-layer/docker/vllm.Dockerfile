FROM vllm/vllm-openai:v0.4.3

ENV MODEL_NAME=TinyLlama/TinyLlama-1.1B-Chat-v1.0
ENV PORT=8000

CMD ["python3", "-m", "vllm.entrypoints.openai.api_server", "--model", "${MODEL_NAME}", "--host", "0.0.0.0", "--port", "${PORT}", "--gpu-memory-utilization", "0.75", "--max-model-len", "2048"]
