FROM python:3.12-bookworm

WORKDIR /app

COPY script.py .

RUN apt update && apt install python3-dev python3-pip -y && \
    pip install --upgrade pip && \
    pip install validators && \
    pip install playwright && \
    playwright install --with-deps && \
    apt clean all

CMD ["python3", "./script.py", "8080"]
EXPOSE 8080
