FROM golang:1.22-alpine AS build
WORKDIR /src
COPY go.mod ./
RUN go mod download
COPY agent ./agent
RUN cd agent && go build -o /bin/aios-agent

FROM alpine:3.20
RUN adduser -D -u 10001 aios
USER aios
COPY --from=build /bin/aios-agent /usr/local/bin/aios-agent
ENTRYPOINT ["/usr/local/bin/aios-agent"]
