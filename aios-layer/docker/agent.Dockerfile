FROM golang:1.22-alpine AS build
WORKDIR /src
COPY go.mod go.sum ./
RUN go mod download
COPY agent/ agent/
COPY config/ config/
RUN go build -o /out/aios-agent ./agent

FROM alpine:3.20
RUN adduser -D aios
USER aios
COPY --from=build /out/aios-agent /usr/local/bin/aios-agent
COPY config/aios.yaml /etc/aios/aios.yaml
EXPOSE 8088
ENTRYPOINT ["aios-agent"]
CMD ["-config", "/etc/aios/aios.yaml"]
