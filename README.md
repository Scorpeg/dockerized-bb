# ScummVM iOS5 buildbot

Requires Linux x86-64, Docker Compose 5.1.3+, Git, Make, and the SDK/toolchain archives.

```sh
bash toolchains/ios5/prepare-inputs.sh /path/iPhoneOS5.1.sdk.zip /path/iOSToolchain-x86_64.tar.xz
make toolchains/ios5
cp .env.example .env
```

Set the fork URL, external token file, and public URL in `.env`. The fork needs `master` and `ios5` branches. The token needs Contents and Workflows write permissions, must be readable by UID 1000, and branch rules must allow rebasing `ios5`.

```sh
docker compose up -d --build
docker compose logs -f
```

One container runs the dashboard, Git sync, compilation, and packaging. Daily at **02:15 Europe/Moscow**, Buildbot updates fork `master`, rebases `ios5`, validates, and builds. Conflicts stop the job; no host cron is needed.

Point nginx at `127.0.0.1:8010`. State and build data persist in Compose volumes. Use `docker compose stop` to stop; `docker compose down` preserves data unless `--volumes` is added. Existing Bash deployments need their state and data migrated before switching.

Run a fresh sync/build now: `docker compose exec buildbot python /bb/scripts/build-now.py`.

App updates: create a persistent RSA key with `openssl genpkey -algorithm RSA -pkeyopt rsa_keygen_bits:3072 -out update-signing.pem`, protect it with `chmod 600 update-signing.pem`, and set `IOS5_UPDATE_SIGNING_KEY_FILE` to its absolute path in `.env`. `IOS5_PUBLIC_URL` must use HTTPS. Keep this key private and backed up; devices trust its public key. Install the first updater-enabled `.deb` manually, then use **Global Options → Misc → Check now**.
