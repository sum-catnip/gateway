FROM lscr.io/linuxserver/wireguard

ENV PYTHONUNBUFFERED=1
RUN apt update && apt install -y python3 python3-pip
ARG LOG_LEVEL=INFO
COPY /root /
COPY /srvgen /app/srvgen
RUN pip3 install -r /app/srvgen/requirements.txt
RUN sh -c "rm /etc/cont-init.d/*confs*"