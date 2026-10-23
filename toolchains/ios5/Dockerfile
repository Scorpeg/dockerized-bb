FROM debian:bookworm-slim@sha256:7b140f374b289a7c2befc338f42ebe6441b7ea838a042bbd5acbfca6ec875818 AS fetch-tools
RUN apt-get update && apt-get install -y --no-install-recommends bash ca-certificates make python3 file xz-utils unzip libtinfo6 libxml2 dpkg-dev gcc g++ autoconf automake libtool libtool-bin pkg-config cmake ninja-build meson patch curl git debhelper gettext bison flex nasm zip && rm -rf /var/lib/apt/lists/*
RUN printf '%s\n' 'deb-src http://deb.debian.org/debian trixie main' > /etc/apt/sources.list.d/scummvm-source.list && apt-get update
FROM fetch-tools AS toolchain
COPY local/iOSToolchain-x86_64.tar.xz /tmp/toolchain.tar.xz
COPY local/iPhoneOS5.1.sdk.zip /tmp/sdk.zip
RUN echo 'a72a7a577e2fbe2838b6b5e9c72034fa7d114af96f0e1d4b016f18730ce4056e  /tmp/toolchain.tar.xz' | sha256sum -c - && echo '451c6ca546c6a9f7bd3257a70547c4b66b9bda420ba11ecc0801424615c7aa92  /tmp/sdk.zip' | sha256sum -c - && mkdir -p /opt/toolchain /opt/sdk && tar -xJf /tmp/toolchain.tar.xz -C /opt/toolchain && unzip -q /tmp/sdk.zip -d /opt/sdk && rm /tmp/toolchain.tar.xz /tmp/sdk.zip
RUN ln -s ranlib /opt/toolchain/linux/iphone/bin/aarch64-apple-darwin14-ranlib
ENV IOS_TOOLCHAIN_BIN=/opt/toolchain/linux/iphone/bin IOS_SDK_ROOT=/opt/sdk/iPhoneOS5.1.sdk SDKROOT=/opt/sdk/iPhoneOS5.1.sdk
COPY scripts /opt/ios5/scripts
COPY vendor /opt/ios5/vendor
COPY packaging /opt/ios5/packaging
COPY full-dependencies.lock.json /opt/ios5/full-dependencies.lock.json
ARG JOBS=6
RUN JOBS=${JOBS} bash /opt/ios5/scripts/build-toolchain.sh
ENV PREFIX=/opt/ios5/build-full/deps CC=/opt/ios5/scripts/cc CXX=/opt/ios5/scripts/cxx AR=/opt/toolchain/linux/iphone/bin/ar RANLIB=/opt/toolchain/linux/iphone/bin/ranlib NM=/opt/toolchain/linux/iphone/bin/nm
ENV PATH=/opt/ios5/build-full/deps/bin:/opt/toolchain/linux/iphone/bin:$PATH PKG_CONFIG_LIBDIR=/opt/ios5/build-full/deps/lib/pkgconfig PKG_CONFIG_PATH="" FLUIDSYNTH_LIBS=-lc++
ENV CPPFLAGS=-I/opt/ios5/build-full/deps/include LDFLAGS=-L/opt/ios5/build-full/deps/lib IOS5_REQUIRE_FULL=1
WORKDIR /build
CMD ["bash", "/opt/ios5/scripts/build-scummvm.sh", "/src", "/build"]
