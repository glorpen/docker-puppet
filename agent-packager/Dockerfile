FROM python:3.8-alpine

RUN pip3 install hvac \
    && rm -rf /root/.cache

COPY entrypoint.py /usr/local/bin/glorpen-entrypoint

ENTRYPOINT [ "glorpen-entrypoint" ]
