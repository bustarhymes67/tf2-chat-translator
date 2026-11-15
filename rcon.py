"""Minimal Source RCON client: how the translator says lines in TF2's chat."""

import socket
import struct


class Rcon:
    """Minimal Source RCON client."""
    AUTH, AUTH_RESPONSE, EXEC, RESPONSE = 3, 2, 2, 0

    def __init__(self, port, password):
        self.addr = ("127.0.0.1", port)
        self.password = password
        self.sock = None
        self.last_id = 100

    def close(self):
        if self.sock:
            self.sock.close()
            self.sock = None

    def connect(self):
        """Connects to TF2 and logs in. A wrong password raises PermissionError."""
        self.close()
        self.sock = socket.create_connection(self.addr, timeout=3)
        self._send(1, self.AUTH, self.password)
        while True:
            rid, kind, _ = self._recv()
            if kind == self.AUTH_RESPONSE:
                if rid == -1:
                    raise PermissionError("wrong RCON password")
                return

    def command(self, cmd):
        """Runs one console command in TF2 and returns what it printed."""
        # Long output comes in several packets. An empty RESPONSE packet sent
        # right after is echoed back once the real output is done.
        cmd_id, end_id = self._next_id(), self._next_id()
        self._send(cmd_id, self.EXEC, cmd)
        self._send(end_id, self.RESPONSE, "")
        out = []
        while True:
            rid, _, body = self._recv()
            if rid == end_id:
                return "".join(out)
            if rid == cmd_id:
                out.append(body)

    def _next_id(self):
        self.last_id += 1
        return self.last_id

    def _send(self, rid, kind, body):
        data = struct.pack("<ii", rid, kind) + body.encode("utf-8") + b"\x00\x00"
        self.sock.sendall(struct.pack("<i", len(data)) + data)

    def _recv_exact(self, n):
        """Reads exactly n bytes: a network read can return less than was asked for."""
        buf = b""
        while len(buf) < n:
            chunk = self.sock.recv(n - len(buf))
            if not chunk:
                raise ConnectionError("RCON connection closed")
            buf += chunk
        return buf

    def _recv(self):
        size = struct.unpack("<i", self._recv_exact(4))[0]
        data = self._recv_exact(size)
        rid, kind = struct.unpack("<ii", data[:8])
        return rid, kind, data[8:-2].decode("utf-8", errors="replace")
