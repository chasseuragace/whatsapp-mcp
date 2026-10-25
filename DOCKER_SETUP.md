# Docker Setup for WhatsApp MCP

Runs the WhatsApp bridge and the MCP server as two long-running containers. Every MCP client
(Claude Code, Claude Desktop, Cursor, ...) connects to the same server by URL, so connecting a
client never starts a new container.

## Architecture

- **whatsapp-bridge**: Go app that logs in to WhatsApp (QR code) and stores messages in SQLite.
- **whatsapp-mcp-server**: Python MCP server, served over Streamable HTTP at
  `http://localhost:8766/mcp`.
- **whatsapp-store volume**: persists the login session, message history and downloaded media.
- **Shared files folder** (`~/WhatsAppFiles` by default): mounted into both containers at the same
  path as on your Mac. Put files here to send them; downloaded media is copied here too.

Both ports are bound to `127.0.0.1`, so nothing else on your network can reach them. The MCP
server also rejects requests whose `Host` or `Origin` isn't localhost, which blocks web pages from
reaching it through DNS rebinding.

## Quick start

1. **Build and start** (from this folder):
   ```bash
   docker compose up -d --build
   ```

2. **Log in**: show the QR code and scan it in WhatsApp → Settings → Linked devices:
   ```bash
   docker compose logs -f whatsapp-bridge
   ```
   If the session has expired (the log says `Device logged out`), restart the bridge to get a new
   QR code: `docker compose restart whatsapp-bridge`.

3. **Connect your MCP clients** to `http://localhost:8766/mcp`:

   **Claude Code**
   ```bash
   claude mcp add --transport http --scope user whatsapp http://localhost:8766/mcp
   ```

   **Claude Desktop** (`~/Library/Application Support/Claude/claude_desktop_config.json`).
   Claude Desktop only launches local commands, so use `mcp-remote` to connect to the URL:
   ```json
   {
     "mcpServers": {
       "whatsapp": {
         "command": "npx",
         "args": ["-y", "mcp-remote", "http://localhost:8766/mcp"]
       }
     }
   }
   ```

   **Cursor** (`~/.cursor/mcp.json`)
   ```json
   {
     "mcpServers": {
       "whatsapp": { "url": "http://localhost:8766/mcp" }
     }
   }
   ```

   Do **not** use `docker compose run ...` as the client command: that creates a new container
   every time the client starts.

## Sending and receiving files

The containers can't see your Mac's files, except the shared folder.

- **Sending**: copy the file into `~/WhatsAppFiles` and pass its full path
  (e.g. `/Users/you/WhatsAppFiles/photo.jpg`) to `send_file` / `send_audio_message`.
- **Downloading**: `download_media` copies the file to `~/WhatsAppFiles/downloads/<chat>/` and
  returns that path.

To use a different folder, set `WHATSAPP_FILES_DIR` (an absolute path) in your shell or in a
`.env` file next to `docker-compose.yml`, then run `docker compose up -d`.

## Voice messages to yourself (`send_self_audio`)

`send_self_audio(text)` speaks the text with your local Piper TTS server (the one the `say`
command starts on `localhost:5000`) and sends it to your own number as a WhatsApp voice note.

- The Piper server must be running on the Mac. If the tool says it can't reach it, run
  `say hello` once to start it.
- Your own number is read from the bridge's login database, so nothing needs configuring.
  Set `WHATSAPP_SELF_JID` to override it.

## Persistence

The `whatsapp-store` volume keeps:
- `whatsapp.db`: WhatsApp login session
- `messages.db`: message history
- `{chat_jid}/`: downloaded media

These survive container restarts and rebuilds. `docker compose down -v` deletes them.

## Commands

- **Start**: `docker compose up -d`
- **Stop**: `docker compose down`
- **Logs**: `docker compose logs -f [whatsapp-bridge|whatsapp-mcp-server]`
- **Rebuild after code changes**: `docker compose up -d --build`
- **Delete all data** (login and history): `docker compose down -v`

## Configuration (MCP server environment)

| Variable | Default | Purpose |
|---|---|---|
| `MCP_TRANSPORT` | `stdio` (`streamable-http` in Compose) | `stdio`, `streamable-http` or `sse` |
| `MCP_HOST` / `MCP_PORT` | `127.0.0.1` / `8000` | Listen address for HTTP transports |
| `MCP_ALLOWED_HOSTS` | `localhost:*,127.0.0.1:*,[::1]:*` | Accepted `Host` headers (comma-separated) |
| `WHATSAPP_API_BASE_URL` | `http://localhost:8080/api` | Bridge REST API |
| `MESSAGES_DB_PATH` | `../whatsapp-bridge/store/messages.db` | Message database |
| `WHATSAPP_FILES_DIR` | unset (`~/WhatsAppFiles` in Compose) | Shared folder for sending/downloading |
| `PIPER_URL` | `http://localhost:5000` (`http://host.docker.internal:5000` in Compose) | Piper TTS server for `send_self_audio` |
| `WHATSAPP_SELF_JID` | read from the bridge's `whatsapp.db` | Your own JID, for `send_self_audio` |
| `WHATSAPP_TMP_DIR` | system temp (`/app/store/tmp` in Compose) | Where converted voice notes are written |

## Troubleshooting

- **Client can't connect**: check `docker compose ps` shows both containers running, and that the
  URL is `http://localhost:8766/mcp`.
- **`421 Misdirected Request`**: the client used a hostname other than `localhost`/`127.0.0.1`.
  Add it to `MCP_ALLOWED_HOSTS`.
- **Bridge not connecting / logged out**: `docker compose logs whatsapp-bridge`; restart the bridge
  and rescan the QR code. WhatsApp unlinks devices that have been inactive for a few weeks.
- **"Media file not found"**: the file isn't inside the shared folder.
