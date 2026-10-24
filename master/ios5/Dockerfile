FROM toolchains/ios5
USER root
RUN apt-get update && apt-get install -y --no-install-recommends python3-venv ccache tzdata && rm -rf /var/lib/apt/lists/*
RUN python3 -m venv /opt/buildbot && /opt/buildbot/bin/pip install --no-cache-dir "buildbot[bundle]==4.3.0" "buildbot-worker==4.3.0" "buildbot-wsgi-dashboards==4.3.0" "bottle==0.13.4"
RUN groupadd -g 1000 buildbot && useradd -m -u 1000 -g buildbot buildbot && mkdir -p /state /data && chown buildbot:buildbot /state /data
COPY buildbot-config /bb/buildbot-config
COPY scripts/web-master.py scripts/sync-ios5.sh scripts/git-askpass.sh /bb/scripts/
ENV PATH=/opt/buildbot/bin:$PATH CCACHE_DIR=/data/ccache
USER buildbot
WORKDIR /state
ENTRYPOINT ["/opt/buildbot/bin/python", "/bb/scripts/web-master.py"]
CMD []
