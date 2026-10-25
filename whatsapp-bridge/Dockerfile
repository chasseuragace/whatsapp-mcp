# Multi-stage build for Go WhatsApp bridge
FROM golang:1.26-alpine3.22 AS builder

WORKDIR /app

# Build dependencies for CGO (needed for SQLite)
RUN apk add --no-cache gcc musl-dev git

# Download dependencies exactly as pinned in go.sum (cached unless they change)
COPY go.mod go.sum ./
RUN go mod download

COPY . .
RUN CGO_ENABLED=1 GOOS=linux go build -o bridge .

# Final stage
FROM alpine:3.22

RUN apk add --no-cache ca-certificates tzdata

WORKDIR /app

COPY --from=builder /app/bridge .

# Persistent data (SQLite databases and media) lives in a volume mounted here
RUN mkdir -p /app/store

EXPOSE 8080

CMD ["./bridge"]
