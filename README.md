# merl-api
An OpenAI-compatible API wrapper for the Merl support agent in the Minecraft Support page. This only supports `/v1/chat/completions` with streaming and non-streaming support.

## Getting started
### Prerequisites
- Docker

### Configuration
By default, the server listens on port 4141 at host 0.0.0.0 and uses DNS of 1.1.1.1 and 8.8.8.8, which can be configured in the `.env` provided in the repo.

## Deployment

### Running with Docker
The easiest way to get the API running is via Docker Compose. This handles the build process and networking configuration automatically.

1. **Clone the repository:**
   ```bash
   git clone https://github.com/quuuut/merl-api.git
   cd merl-api
   ```
2. **Start the container:**
   ```bash
   docker compose up -d
   ```

## API Usage
The server has been made to comply with the OpenAI `/v1/chat/completions` API for easy client use and supports response streaming.

### Example Request
```bash
curl http://localhost:4141/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "merl",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```

## Contributing
Contributions are welcome! Please feel free to open a PR in order to fix or add features that you would like!

## License
Distributed under the Apache License 2.0. See LICENSE for more information.
