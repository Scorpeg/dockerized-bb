# ScummVM iOS5 buildbot

Docker cross-build for jailbroken iOS 5.1 ARMv7. Requires Linux x86-64, Docker, Git, Make, m4, and the SDK/toolchain archives.

```sh
bash toolchains/ios5/prepare-inputs.sh /path/iPhoneOS5.1.sdk.zip /path/iOSToolchain-x86_64.tar.xz
make toolchains/ios5 workers/ios5 workers/fetcher
```
