# 使用Python 3.10官方镜像作为基础镜像
FROM python:3.10

WORKDIR /app

COPY requirements.txt ./
RUN pip install --upgrade pip && pip install setuptools wheel && pip install -r requirements.txt
RUN apt-get update && apt-get install -y libgl1-mesa-glx libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

ENV HF_ENDPOINT="https://hf-mirror.com"
COPY . .
RUN python init_text_img_model.py

CMD ["streamlit", "run", "app.py"]

# 暴露Streamlit默认运行端口
EXPOSE 8501