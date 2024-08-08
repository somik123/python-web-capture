FROM python:3.12-bookworm

WORKDIR /app

COPY script.py .
COPY favicon.ico .

RUN apt update && apt install python3-dev python3-pip -y && \
    pip install --upgrade pip && \
    pip install validators && \
    pip install playwright && \
    playwright install --with-deps && \
    apt clean all

CMD ["python3", "-u", "script.py", "8080"]

EXPOSE 8080
