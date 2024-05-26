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

3. Get container id of `streamlit-app`:

```shell
> docker ps
> CONTAINER ID     IMAGE            COMMAND
  <container_id>   streamlit-app    "tail -f /dev/null"
```

4. After `boot success!`, open a bash with:

```shell
docker exec -it <container_id> bash
```

5. start streamlit app

```shell
streamlit run app.py
```

6. Visit `localhost:8501`