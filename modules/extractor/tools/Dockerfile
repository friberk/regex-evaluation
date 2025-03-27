# use a rusty image
FROM ubuntu:24.04

# Use bash instead of sh
SHELL ["/bin/bash", "--login", "-c"]

###############################
# install a bunch of packages #
###############################
RUN apt update --fix-missing
RUN apt install -y \
    bzip2 ca-certificates curl git libc-bin make openssl python3 node-gyp \
    openjdk-17-jdk openjdk-21-jdk openjdk-8-jdk wget sqlite3 libsqlite3-dev \
    python3-dev maven cloc libxml2-dev pkg-config jetty9

########################
# Install NVM and such #
########################
RUN mkdir /usr/local/nvm
ENV NVM_DIR /usr/local/nvm
RUN curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash \
	&& . $NVM_DIR/nvm.sh \
	&& nvm install v20.11.1 \
	&& nvm install v18.19.0 \
	&& nvm install v16.20.2 \
	&& nvm alias default v20.11.1 \
	&& nvm use default

# Install yarn v3
RUN . $NVM_DIR/nvm.sh && corepack enable && corepack install -g yarn@3

##########################
# Add stuff to your path #
##########################
ENV BASE_NODE_PATH $NVM_DIR/versions/node/v20.11.1
ENV NODE_PATH      $BASE_NODE_PATH/lib/node_modules
ENV PATH           $BASE_NODE_PATH/bin:$PATH

# Magic rust stuff. don't touch
ENV RUSTUP_HOME=/usr/local/rustup \
    CARGO_HOME=/usr/local/cargo \
    PATH=/usr/local/cargo/bin:$PATH \
    RUST_VERSION=1.76.0

RUN set -eux; \
    dpkgArch="$(dpkg --print-architecture)"; \
    case "${dpkgArch##*-}" in \
        amd64) rustArch='x86_64-unknown-linux-gnu'; rustupSha256='0b2f6c8f85a3d02fde2efc0ced4657869d73fccfce59defb4e8d29233116e6db' ;; \
        armhf) rustArch='armv7-unknown-linux-gnueabihf'; rustupSha256='f21c44b01678c645d8fbba1e55e4180a01ac5af2d38bcbd14aa665e0d96ed69a' ;; \
        arm64) rustArch='aarch64-unknown-linux-gnu'; rustupSha256='673e336c81c65e6b16dcdede33f4cc9ed0f08bde1dbe7a935f113605292dc800' ;; \
        i386) rustArch='i686-unknown-linux-gnu'; rustupSha256='e7b0f47557c1afcd86939b118cbcf7fb95a5d1d917bdd355157b63ca00fc4333' ;; \
        ppc64el) rustArch='powerpc64le-unknown-linux-gnu'; rustupSha256='1032934fb154ad2d365e02dcf770c6ecfaec6ab2987204c618c21ba841c97b44' ;; \
        *) echo >&2 "unsupported architecture: ${dpkgArch}"; exit 1 ;; \
    esac; \
    url="https://static.rust-lang.org/rustup/archive/1.26.0/${rustArch}/rustup-init"; \
    wget "$url"; \
    echo "${rustupSha256} *rustup-init" | sha256sum -c -; \
    chmod +x rustup-init; \
    ./rustup-init -y --no-modify-path --profile minimal --default-toolchain $RUST_VERSION --default-host ${rustArch}; \
    rm rustup-init; \
    chmod -R a+w $RUSTUP_HOME $CARGO_HOME; \
    rustup --version; \
    cargo --version; \
    rustc --version;
# end magic rust stuff

###########################################
# Copy in and build java static extractor #
###########################################
COPY ./java-static-extractor /app/static-extractors/java
WORKDIR /app/static-extractors/java
RUN ./gradlew installDist
ENV JAVA_EXTRACTOR_PATH=/app/static-extractors/java/app/build/install/app/bin/app

############################################
# Copy in and build java dynamic extractor #
############################################
COPY ./jde-agent /app/dynamic-extractors/java
WORKDIR /app/dynamic-extractors/java
RUN mvn package
ENV JDE_AGENT_PATH=/app/dynamic-extractors/java/target/jde-agent-1.0-SNAPSHOT-jar-with-dependencies.jar

#######################################
# Copy in javascript static extractor #
#######################################
COPY ./javascript-static-extractor /app/static-extractors/js
WORKDIR /app/static-extractors/js
RUN . $NVM_DIR/nvm.sh && npm install
RUN . $NVM_DIR/nvm.sh && npm run bundle
ENV JS_EXTRACTOR_PATH=/app/static-extractors/js/bin/js-static-extractor.js

###################################
# Copy in python static extractor #
###################################
COPY ./python-static-extractor /app/static-extractors/python
WORKDIR /app/static-extractors/python
ENV PYTHON_EXTRACTOR_PATH=/app/static-extractors/python/extract-regexps.py

#############################
# Copy in monkeypatch stuff #
#############################
COPY ./monkeypatch-regex /app/monkeypatch
ENV JS_MONKEYPATCH_PATH=/app/monkeypatch/monkey-regexp.js
ENV TS_MONKEYPATCH_PATH=/app/monkeypatch/monkey-regexp.ts

ENTRYPOINT . $NVM_DIR/nvm.sh && /bin/bash
