# 使用Python 3.10官方镜像作为基础镜像
FROM python:3.10

WORKDIR /app

COPY requirements.txt ./
RUN pip install --upgrade pip && pip install --no-cache-dir setuptools wheel && pip install --no-cache-dir -r requirements.txt
COPY . .
RUN apt-get update && apt-get install -y libgl1-mesa-glx \
    && rm -rf /var/lib/apt/lists/*
RUN apt-get install -y libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

ENV HF_ENDPOINT="https://hf-mirror.com"

CMD ["tail", "-f", "/dev/null"]

# 暴露Streamlit默认运行端口
EXPOSE 8501