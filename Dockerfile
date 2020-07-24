FROM ubuntu:20.10
RUN apt-get update && \
    apt-get -y install python3.8 python3-pip && \
    rm -rf /var/lib/apt/lists/*
RUN echo y | pip3 install watchdog==0.10.2 pathtools==0.1.2
COPY hotspud /hotspud/
ENTRYPOINT /usr/bin/python3.8 /hotspud/hotspud.py
