FROM alpine:latest

LABEL maintainer="sergio@fernandezcordero.net"

# Environment and dependencies
RUN apk update && \
    apk add bash python3 py3-pip ca-certificates wget gcc python3-dev musl-dev libffi-dev openssl-dev && \
    update-ca-certificates && \
    rm -f /var/cache/apk/* && \
    rm /bin/sh && \
    ln -s /bin/bash /bin/sh && \
    mkdir -p /opt/raponchi && \
    addgroup aenea --gid 1001 && \
    adduser -g raponchi -G raponchi -h /opt/raponchi -D raponchi -u 1001 && \
    mkdir -p /opt/raponchi/
# Deploy
ADD raponchi/* /opt/raponchi/
RUN chown -R raponchi:raponchi /opt/raponchi && \
    pip3 install -r /opt/raponchi/requirements.txt
# Run
USER raponchi
CMD python3 /opt/raponchi/raponchi.py
