FROM toolchains/ios5
ARG BUILDBOT_VERSION=4.3.0
RUN apt-get update && apt-get install -y --no-install-recommends dumb-init python3-venv python3-wheel ccache && rm -rf /var/lib/apt/lists/*
RUN python3 -m venv /opt/buildbot && /opt/buildbot/bin/pip install --no-cache-dir buildbot-worker==${BUILDBOT_VERSION}
ARG BUILDBOT_UID=1000
ARG BUILDBOT_GID=1000
LABEL buildbot-uid=${BUILDBOT_UID} buildbot-gid=${BUILDBOT_GID} buildbot-version=${BUILDBOT_VERSION}
RUN groupadd -g ${BUILDBOT_GID} buildbot && useradd -g ${BUILDBOT_GID} -u ${BUILDBOT_UID} buildbot && mkdir -p /buildbot-worker /data/bshomes /data/build /data/ccache /data/src && chown -R buildbot:buildbot /buildbot-worker /data
ADD https://raw.githubusercontent.com/buildbot/buildbot/v${BUILDBOT_VERSION}/worker/docker/buildbot.tac /buildbot-worker/buildbot.tac
RUN chmod 644 /buildbot-worker/buildbot.tac
ENV CCACHE_DIR=/data/ccache
USER buildbot
WORKDIR /buildbot-worker
VOLUME /data/bshomes /data/build /data/ccache /data/src
ENTRYPOINT ["/usr/bin/dumb-init", "/opt/buildbot/bin/twistd", "--pidfile=", "-ny", "buildbot.tac"]
