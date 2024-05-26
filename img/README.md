# An img2img demo for OceanBase Vector Store

## How to deploy demo with docker?

1. Build docker image.

```shell
docker build -t streamlit-app .
```

2. Run docker image with docker-compose.

```shell
docker-compose up
```

3. After `boot success!`, open a bash with:

```shell
docker exec -it streamlit-app bash
```

4. start streamlit app

```shell
streamlit run app.py
```

5. Visit `localhost:8501`