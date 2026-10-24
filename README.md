# ScummVM iOS5 buildbot

Builds ScummVM for jailbroken iOS 5.1 ARMv7 devices. Requires Linux x86-64, Docker, Git, Make, m4, and the SDK/toolchain archives.

```sh
bash toolchains/ios5/prepare-inputs.sh /path/iPhoneOS5.1.sdk.zip /path/iOSToolchain-x86_64.tar.xz
make toolchains/ios5 workers/ios5 workers/fetcher
bash check-ios5-config.sh
docker build -t masters/ios5 -f master/ios5/Dockerfile master/ios5

export IOS5_REPOSITORY=https://github.com/YOUR_ACCOUNT/scummvm.git
export IOS5_GIT_TOKEN_FILE=/path/private/github-token
export IOS5_PUBLIC_URL=https://buildbot.example.org/
bash start-ios5-web.sh start
```

The fork must have `master` and `ios5` branches. The token needs Contents and Workflows write permissions; branch rules must allow rebasing `ios5`. Keep the token outside this repository.

Daily at **02:15 Europe/Moscow**: update fork `master`, rebase `ios5`, validate, then build and package. Conflicts stop the job. The dashboard listens on `127.0.0.1:8010`; configure your reverse proxy separately.

Data defaults to `buildbot-data`; override with `IOS5_DATA_DIR`. Use `bash start-ios5-web.sh status` or `stop` to manage the service. Recreate the container after changing environment settings, retaining its data directories.
