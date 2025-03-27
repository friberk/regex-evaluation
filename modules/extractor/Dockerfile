FROM anonymous/regex-extractor-base:1.4.0

WORKDIR /app/extractor
COPY . .

RUN cargo build --release --no-default-features --features=extractor -p driver -p python-static-extractor-v2

# Add stuff for python
ENV PYTHON_EXTRACTOR_PATH=/app/extractor/target/release/python-static-extractor-v2
ENV PYTHON_STATIC_EXTRACTOR_MODULE_PATH=/app/extractor/tools/python-static-extractor-v2/src/python_static_extractor.py

# Delete all source (except for tools)
RUN rm -rf combiner db docs driver dynamic-extraction ecosystems-dump evaluation reporting shared static-extraction

ENTRYPOINT [ "/app/extractor/target/release/driver" ]
