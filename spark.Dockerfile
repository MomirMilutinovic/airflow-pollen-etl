FROM bitnami/spark:3.5.5

RUN pip install cyrtranslit==1.1.1
RUN pip install aiohttp==3.11.17
