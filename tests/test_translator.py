"""The translator's own logic. Nothing here touches your config.json or the internet."""
import os
import queue
import sys
import tempfile
import threading
import time
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import translator  # noqa: E402

translator.CONFIG_PATH = os.path.join(tempfile.mkdtemp(), "config.json")


def run_worker(cfg, lines, said=None):
    asked, results = [], queue.Queue()

    def fake(text, target):
        asked.append(text)
        return "translated", "xx"
    real, translator.translate_chat = translator.translate_chat, fake
    q = queue.Queue()
    threading.Thread(target=translator.worker, args=(cfg, q, results, said), daemon=True).start()
    try:
        for line in lines:
            q.put(line)
        time.sleep(0.5)
    finally:
        translator.translate_chat = real
    return asked, [results.get() for _ in range(results.qsize())]


class WorkerTest(unittest.TestCase):
    LINES = ["Ivan :  привет всем ребята", "Juan :  hola amigos que tal", "Bob :  nice shot man"]

    def test_russian_only(self):
        asked, _ = run_worker(dict(translator.DEFAULTS, languages="russian"), self.LINES)
        self.assertEqual(asked, ["привет всем ребята"])

    def test_all_languages_but_english(self):
        asked, _ = run_worker(dict(translator.DEFAULTS, languages="all"), self.LINES)
        self.assertEqual(asked, ["привет всем ребята", "hola amigos que tal"])

    def test_short_russian_without_google(self):
        asked, out = run_worker(dict(translator.DEFAULTS), ["(TEAM) Ivan :  стой"])
        self.assertEqual(asked, [])
        self.assertEqual((out[0]["text"], out[0]["team"]), ("wait", True))

    def test_our_own_chat_line_is_not_translated_again(self):
        asked, _ = run_worker(dict(translator.DEFAULTS), ["Me :  Juan says: hola amigos que tal"],
                              said={"Juan says: hola amigos que tal"})
        self.assertEqual(asked, [])


class ChatTest(unittest.TestCase):
    def entry(self, name, text, team=False):
        return {"name": name, "text": text, "team": team}

    def test_waiting_lines_are_joined_per_chat(self):
        waiting = [self.entry("A", "hi"), self.entry("B", "go"), self.entry("C", "push", team=True)]
        self.assertEqual(translator.next_chat_line(waiting), ("say", "A says: hi | B says: go"))
        self.assertEqual(translator.next_chat_line(waiting), ("say_team", "C says: push"))
        self.assertEqual(waiting, [])

    def test_lines_fit_tf2s_limit_and_cant_break_the_command(self):
        command, text = translator.next_chat_line([self.entry('x"; quit', "word " * 60)])
        self.assertTrue(translator.fits(text))
        self.assertNotIn('"', text)
        self.assertNotIn(";", text)

    def test_spam_limit_lets_a_burst_through_then_slows_down(self):
        limit, now, sent = translator.ChatLimit(), time.time() + 100, []
        t = now
        while t < now + 30:
            if limit.wait(t) == 0:
                limit.note(t)
                sent.append(t)
            t += 0.1
        self.assertGreaterEqual(len(sent), 9)
        self.assertLessEqual(len(sent), 14)


class RconTest(unittest.TestCase):
    def test_says_a_line_over_rcon(self):
        import socket
        import struct
        server = socket.socket()
        server.bind(("127.0.0.1", 0))
        server.listen(1)
        got = []

        def serve():
            conn, _ = server.accept()

            def recv():
                size = struct.unpack("<i", conn.recv(4))[0]
                data = b""
                while len(data) < size:
                    data += conn.recv(size - len(data))
                rid, kind = struct.unpack("<ii", data[:8])
                return rid, kind, data[8:-2].decode()

            def send(rid, kind, body=""):
                data = struct.pack("<ii", rid, kind) + body.encode() + b"\x00\x00"
                conn.sendall(struct.pack("<i", len(data)) + data)
            rid, _, pw = recv()
            send(rid if pw == "pw" else -1, 2)
            while True:
                try:
                    rid, kind, body = recv()
                except Exception:
                    return
                got.append(body) if body else None
                send(rid, 0)
        threading.Thread(target=serve, daemon=True).start()
        cfg = dict(translator.DEFAULTS, rcon_port=server.getsockname()[1], rcon_password="pw")
        entries, status = queue.Queue(), queue.Queue()
        threading.Thread(target=translator.chat_sender, args=(cfg, entries, set(), status), daemon=True).start()
        entries.put({"name": "Ivan", "text": "wait", "team": False})
        deadline = time.time() + 5
        while time.time() < deadline and not got:
            time.sleep(0.05)
        self.assertEqual(got, ['say "Ivan says: wait"'])


if __name__ == "__main__":
    unittest.main()
