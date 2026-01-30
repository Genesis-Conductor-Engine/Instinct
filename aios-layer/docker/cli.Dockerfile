FROM golang:1.22-alpine AS build
WORKDIR /src
COPY go.mod go.sum ./
RUN go mod download
COPY cli/ cli/
RUN go build -o /out/aiosctl ./cli

FROM alpine:3.20
RUN adduser -D aios
USER aios
COPY --from=build /out/aiosctl /usr/local/bin/aiosctl
ENTRYPOINT ["aiosctl"]
