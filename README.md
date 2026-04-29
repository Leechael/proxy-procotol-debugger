# Proxy Protocol Debugger

A lightweight Python tool for debugging and inspecting [Proxy Protocol](https://www.haproxy.org/download/1.8/doc/proxy-protocol.txt) headers. Supports both V1 (text) and V2 (binary) formats.

## Features

- Parse and display Proxy Protocol V1 & V2 headers
- Show raw bytes and hex dump of incoming PROXY data
- Return the extracted client IP via a simple HTTP response
- Useful for verifying that your load balancer or proxy is sending correct PROXY headers

## Quick Start

### Docker

```bash
docker run --rm -p 8888:8888 ghcr.io/leechael/proxy-procotol-debugger:latest
```

### Manual

```bash
python3 main.py
```

The server listens on `0.0.0.0:8888`.

## Testing

### Proxy Protocol V1

```bash
echo -e "PROXY TCP4 1.2.3.4 5.6.7.8 1234 80\r\n" | nc 127.0.0.1 8888
```

### Proxy Protocol V2

Use any tool that can send binary PROXY v2 headers, or test through a real load balancer (e.g., AWS NLB, HAProxy, Nginx) configured with Proxy Protocol.

## Output Example

```
New connection accepted
Received initial bytes: b'PROXY TCP4 1.2.3.4 5.6.7.8 1234 80\r\n'
Received initial bytes hex: 50524f5459205443503420312e322e332e3420352e362e372e3820313233342038300d0a
Parsed Proxy Info: {'protocol': 'TCP4', 'src_ip': '1.2.3.4', 'dst_ip': '5.6.7.8', 'src_port': '1234', 'dst_port': '80'}
Connection closed
```

## License

MIT License — see [LICENSE](LICENSE) for details.
