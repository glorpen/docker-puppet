FROM python:3.8-alpine

RUN apk add -t .dev gcc musl-dev libffi-dev openssl-dev \
    && apk add openssl libffi \
    && pip3 install hvac==0.10.4 cryptography==2.9.2 \
    && apk del --purge .dev \
    && rm -rf /root/.cache /var/cache/apk/*

COPY glorpen_entrypoint/ /usr/local/lib/python3.8/site-packages/glorpen_entrypoint/
COPY agent-packager/entrypoint.py /usr/local/lib/python3.8/site-packages/glorpen_entrypoint/__main__.py

ENTRYPOINT ["python3", "-m", "glorpen_entrypoint"]
