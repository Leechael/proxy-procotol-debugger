import asyncio
import ipaddress

PP2_MAGIC = b"\r\n\r\n\0\r\nQUIT\n"
PP2_HEADER_LEN = 16
PP2_TCP4 = 0x11
PP2_TCP6 = 0x21

# Basic Proxy Protocol V1 parser
def parse_proxy_line(line: bytes):
    try:
        line_str = line.decode('utf-8').strip()
    except UnicodeDecodeError:
        return None
        
    parts = line_str.split(' ')
    if len(parts) != 6 or parts[0] != 'PROXY':
        return None
    
    return {
        "protocol": parts[1],
        "src_ip": parts[2],
        "dst_ip": parts[3],
        "src_port": parts[4],
        "dst_port": parts[5]
    }

def parse_proxy_v2(header: bytes):
    if len(header) < PP2_HEADER_LEN or not header.startswith(PP2_MAGIC):
        return None

    ver_cmd = header[12]
    fam_proto = header[13]
    payload_len = int.from_bytes(header[14:16], "big")
    payload = header[16:16 + payload_len]

    if ver_cmd >> 4 != 0x2:
        return None
    if ver_cmd & 0x0f != 0x1:
        return {
            "version": "v2",
            "protocol": "LOCAL",
            "src_ip": "<local>",
            "dst_ip": "<local>",
            "src_port": "0",
            "dst_port": "0",
        }

    if fam_proto == PP2_TCP4 and len(payload) >= 12:
        src_ip = str(ipaddress.IPv4Address(payload[0:4]))
        dst_ip = str(ipaddress.IPv4Address(payload[4:8]))
        src_port = int.from_bytes(payload[8:10], "big")
        dst_port = int.from_bytes(payload[10:12], "big")
        protocol = "TCP4"
    elif fam_proto == PP2_TCP6 and len(payload) >= 36:
        src_ip = str(ipaddress.IPv6Address(payload[0:16]))
        dst_ip = str(ipaddress.IPv6Address(payload[16:32]))
        src_port = int.from_bytes(payload[32:34], "big")
        dst_port = int.from_bytes(payload[34:36], "big")
        protocol = "TCP6"
    else:
        return {
            "version": "v2",
            "protocol": f"0x{fam_proto:02x}",
            "src_ip": "<unsupported>",
            "dst_ip": "<unsupported>",
            "src_port": "0",
            "dst_port": "0",
        }

    return {
        "version": "v2",
        "protocol": protocol,
        "src_ip": src_ip,
        "dst_ip": dst_ip,
        "src_port": str(src_port),
        "dst_port": str(dst_port),
    }

async def read_proxy_header(reader):
    first = await reader.readexactly(1)

    if first == b"P":
        rest = await reader.readuntil(b"\r\n")
        line = first + rest
        return line, parse_proxy_line(line)

    rest = await reader.readexactly(PP2_HEADER_LEN - 1)
    prefix = first + rest
    if prefix.startswith(PP2_MAGIC):
        payload_len = int.from_bytes(prefix[14:16], "big")
        payload = await reader.readexactly(payload_len)
        header = prefix + payload
        return header, parse_proxy_v2(header)

    return prefix, None

def write_http_response(writer, body: str):
    body_bytes = body.encode()
    writer.write(
        b"HTTP/1.1 200 OK\r\n"
        b"Content-Type: text/plain; charset=utf-8\r\n"
        + f"Content-Length: {len(body_bytes)}\r\n".encode()
        + b"Connection: close\r\n"
        + b"\r\n"
        + body_bytes
    )

async def handle_client(reader, writer):
    print("New connection accepted", flush=True)
    
    try:
        data, proxy_info = await read_proxy_header(reader)
        print(f"Received initial bytes: {data!r}", flush=True)
        print(f"Received initial bytes hex: {data.hex()}", flush=True)
        
        if proxy_info:
            print(f"Parsed Proxy Info: {proxy_info}", flush=True)
            write_http_response(
                writer,
                f"Hello {proxy_info['src_ip']} (via Proxy Protocol {proxy_info.get('version', 'v1')})\n",
            )
        else:
            print("Direct connection detected (no PROXY header).", flush=True)
            write_http_response(writer, "Hello (Direct Connection)\n")
        
        await writer.drain()
    except Exception as e:
        print(f"Error handling client: {e}", flush=True)
    finally:
        writer.close()
        await writer.wait_closed()
        print("Connection closed", flush=True)

async def main():
    server = await asyncio.start_server(handle_client, '0.0.0.0', 8888)
    print("Server running on 0.0.0.0:8888", flush=True)
    async with server:
        await server.serve_forever()

if __name__ == '__main__':
    asyncio.run(main())
