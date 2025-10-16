FROM otel/opentelemetry-collector-contrib:0.100.0

COPY otel-config.yaml /etc/otel/otel-config.yaml

EXPOSE 4317 4318 8888 8889 13133

CMD ["--config=/etc/otel/otel-config.yaml"]
