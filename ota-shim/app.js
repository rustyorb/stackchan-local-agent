const crypto = require("crypto");
const http = require("http");

const host = process.env.HOST || "0.0.0.0";
const port = Number(process.env.PORT || 8003);
const publicUrl = (process.env.PUBLIC_URL || `http://192.168.0.250:${port}`).replace(/\/+$/, "");
const firmwareVersion = process.env.FIRMWARE_VERSION || "1.2.6-dev";
const protocolVersion = Number(process.env.PROTOCOL_VERSION || 3);

function websocketUrl(path = "/xiaozhi/v1/") {
  return publicUrl.replace(/^http:\/\//, "ws://").replace(/^https:\/\//, "wss://") + path;
}

function otaPayload(path = "/xiaozhi/v1/") {
  return {
    server_time: {
      timestamp: Date.now(),
      timezone_offset: 0,
    },
    firmware: {
      version: firmwareVersion,
      url: "",
    },
    websocket: {
      url: websocketUrl(path),
      token: "dev",
      version: protocolVersion,
    },
  };
}

function sendJson(res, status, payload) {
  const body = JSON.stringify(payload);
  res.writeHead(status, {
    "content-type": "application/json",
    "content-length": Buffer.byteLength(body),
  });
  res.end(body);
}

function sendWsText(socket, text) {
  const payload = Buffer.from(text);
  let header;
  if (payload.length < 126) {
    header = Buffer.from([0x81, payload.length]);
  } else if (payload.length < 65536) {
    header = Buffer.alloc(4);
    header[0] = 0x81;
    header[1] = 126;
    header.writeUInt16BE(payload.length, 2);
  } else {
    throw new Error("payload too large");
  }
  socket.write(Buffer.concat([header, payload]));
}

function parseWsFrames(buffer) {
  const frames = [];
  let offset = 0;
  while (offset + 2 <= buffer.length) {
    const b0 = buffer[offset];
    const b1 = buffer[offset + 1];
    const opcode = b0 & 0x0f;
    const masked = (b1 & 0x80) !== 0;
    let len = b1 & 0x7f;
    offset += 2;
    if (len === 126) {
      if (offset + 2 > buffer.length) break;
      len = buffer.readUInt16BE(offset);
      offset += 2;
    } else if (len === 127) {
      console.warn("WS frame too large; closing");
      return frames;
    }
    let mask;
    if (masked) {
      if (offset + 4 > buffer.length) break;
      mask = buffer.subarray(offset, offset + 4);
      offset += 4;
    }
    if (offset + len > buffer.length) break;
    const payload = Buffer.from(buffer.subarray(offset, offset + len));
    offset += len;
    if (masked && mask) {
      for (let i = 0; i < payload.length; i++) payload[i] ^= mask[i % 4];
    }
    frames.push({ opcode, payload });
  }
  return frames;
}

const server = http.createServer((req, res) => {
  const chunks = [];
  req.on("data", (chunk) => chunks.push(chunk));
  req.on("end", () => {
    const body = Buffer.concat(chunks).toString("utf8").slice(0, 300);
    if (req.url === "/v1/ota" || req.url === "/xiaozhi/v1/ota" || req.url === "/xiaozhi/ota/" || req.url === "/xiaozhi/ota") {
      console.log(`[ota] ${req.method} ${req.url} device=${req.headers["device-id"] || "?"} body=${body}`);
      sendJson(res, 200, otaPayload(req.url === "/v1/ota" ? "/v1/" : "/xiaozhi/v1/"));
      return;
    }
    res.writeHead(404, { "content-type": "text/plain" });
    res.end("not found\n");
  });
});

server.on("upgrade", (req, socket) => {
  if (req.url !== "/v1/" && req.url !== "/v1" && req.url !== "/xiaozhi/v1/" && req.url !== "/xiaozhi/v1") {
    socket.end("HTTP/1.1 404 Not Found\r\n\r\n");
    return;
  }

  const key = req.headers["sec-websocket-key"];
  if (!key) {
    socket.end("HTTP/1.1 400 Bad Request\r\n\r\n");
    return;
  }

  const accept = crypto
    .createHash("sha1")
    .update(key + "258EAFA5-E914-47DA-95CA-C5AB0DC85B11")
    .digest("base64");

  socket.write(
    "HTTP/1.1 101 Switching Protocols\r\n" +
      "Upgrade: websocket\r\n" +
      "Connection: Upgrade\r\n" +
      `Sec-WebSocket-Accept: ${accept}\r\n\r\n`
  );

  const sessionId = crypto.randomBytes(8).toString("hex");
  console.log(
    `[ws] open device=${req.headers["device-id"] || "?"} client=${req.headers["client-id"] || "?"} proto=${
      req.headers["protocol-version"] || "?"
    }`
  );

  socket.on("data", (buffer) => {
    for (const frame of parseWsFrames(buffer)) {
      if (frame.opcode === 1) {
        const text = frame.payload.toString("utf8");
        console.log(`[ws] text <- ${text.slice(0, 500)}`);
        try {
          const obj = JSON.parse(text);
          if (obj.type === "hello") {
            const hello = {
              type: "hello",
              transport: "websocket",
              session_id: sessionId,
              audio_params: {
                sample_rate: 16000,
                frame_duration: 60,
              },
            };
            sendWsText(socket, JSON.stringify(hello));
            console.log(`[ws] text -> hello session=${sessionId}`);
          }
        } catch (err) {
          console.warn(`[ws] bad json: ${err.message}`);
        }
      } else if (frame.opcode === 2) {
        console.log(`[ws] binary <- ${frame.payload.length} bytes`);
      } else if (frame.opcode === 8) {
        socket.end();
      }
    }
  });

  socket.on("close", () => console.log(`[ws] close session=${sessionId}`));
});

server.listen(port, host, () => {
  console.log(`[server-xz-node] listening on ${host}:${port}`);
  console.log(`[server-xz-node] OTA: ${publicUrl}/v1/ota`);
  console.log(`[server-xz-node] OTA: ${publicUrl}/xiaozhi/ota/`);
  console.log(`[server-xz-node] OTA: ${publicUrl}/xiaozhi/v1/ota`);
  console.log(`[server-xz-node] WS:  ${websocketUrl("/v1/")}`);
  console.log(`[server-xz-node] WS:  ${websocketUrl("/xiaozhi/v1/")}`);
});
