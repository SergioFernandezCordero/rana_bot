FROM alpine:latest

LABEL maintainer="sergio@fernandezcordero.net"

# Environment and dependencies
RUN apk update && \
    apk add bash python3 py3-pip ca-certificates wget gcc python3-dev musl-dev libffi-dev openssl-dev tzdata && \
    update-ca-certificates && \
    rm -f /var/cache/apk/* && \
    rm /bin/sh && \
    ln -s /bin/bash /bin/sh && \
    mkdir -p /opt/raponchi && \
    addgroup raponchi --gid 1001 && \
    adduser -g raponchi -G raponchi -h /opt/raponchi -D raponchi -u 1001 && \
    mkdir -p /opt/raponchi/ && \
    mkdir -p /opt/raponchi/venv/

# Deploy
ADD raponchi/* /opt/raponchi/
ADD raponchi/scripts/run_raponchi.sh /opt/raponchi/
RUN chown -R raponchi:raponchi /opt/raponchi && \
    chmod +x /opt/raponchi/run_raponchi.sh && \
    # Using a virtualenv like nice people do
    python3 -m venv /opt/raponchi/venv && \
    . /opt/raponchi/venv/bin/activate && \
    pip3 install -r /opt/raponchi/requirements.txt
# Run
USER raponchi
ENTRYPOINT ["/opt/raponchi/run_raponchi.sh"]
