#!/usr/bin/env python3
# newsboat_pty.py -- the spark macro inside a real newsboat, in a pty,
# against a stub `spark` (on PATH: the wrapper says `spark` plainly, and
# that is what must be proven) that logs what it was asked and answers a
# fixed word. Proves the loop the snippet promises: ,s pipes the RENDERED
# article (header and text, never a path) through `spark-newsboat` on the
# terminal newsboat hands over, the words reach `spark read` with the
# article on stdin, a refusal on spark's stderr still shows on screen
# (the wrapper folds it in), Ctrl-C runs nothing, and newsboat is alive
# and navigable after every exchange. The test performs the README's
# install lines: config.spark appended to a fresh config and the wrapper
# put on PATH. Skips (exit 0) without newsboat.
#
#   python3 tests/newsboat_pty.py

import fcntl
import os
import re
import pty
import select
import shutil
import struct
import subprocess
import sys
import tempfile
import termios
import time

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSI = re.compile(r"\x1b(?:\[[0-9;?]*[ -/]*[@-~]|\([A-Za-z0-9]|\][^\x07\x1b]*(?:\x07|\x1b\\)|[@-Z\\-_])")

STUB = r'''#!/bin/sh
# the stub spark: log argv and stdin, answer one word per verb --
# STUB-READ for read, STUB-EDIT for edit. `reveal` is the pass-through
# pacer (1.31+): -h says it exists, otherwise copy -- and it never
# touches the log, so the argv assertions stay about the verbs.
case ${1-} in
    reveal) [ "${2-}" = "-h" ] && exit 0; exec cat ;;
esac
printf '%s\n' "$*" >> "$STUB_LOG"
cat > "$STUB_LOG.stdin"
case " $* " in
    *" fail "*)   printf 'spark: the source does not answer -- it opens: "STUB-OPENING ..."\n' >&2; exit 1 ;;
    *" long "*)   i=0; while [ $i -lt 40 ]; do printf 'wrapword '; i=$((i+1)); done; printf '\n'; exit 0 ;;
esac
case ${1-} in
    edit) printf 'STUB-EDIT with a mark [not in the text]' ;;   # NO trailing newline: raw stream
    *)    printf 'STUB-READ\n' ;;
esac
'''

FEED = """<?xml version="1.0"?>
<rss version="2.0"><channel><title>probe feed</title>
<link>http://192.0.2.1/</link><description>probe</description>
<item><title>the gate article</title><link>http://192.0.2.1/a</link>
<description>The gate opens at nine and closes at noon.
Tickets are two dollars, free for children. The orchard stall sells
cider on weekends through October, and the west meadow is open for
picnics whenever the flag is up by the old gate.</description></item>
</channel></rss>
"""

STUBFEED = """<?xml version="1.0"?>
<rss version="2.0"><channel><title>stub feed</title>
<link>http://192.0.2.1/s</link><description>stubs</description>
<item><title>a link only</title><link>http://192.0.2.1/b</link>
<description>Comments: http://192.0.2.1/c</description></item>
</channel></rss>
"""


class Reader:
    def __init__(self, argv, env, cwd, rows=30, cols=100):
        self.buf = b""
        self.pos = 0
        pid, fd = pty.fork()
        if pid == 0:
            os.chdir(cwd)
            os.execvpe(argv[0], argv, env)
        self.pid, self.fd = pid, fd
        fcntl.ioctl(fd, termios.TIOCSWINSZ, struct.pack("HHHH", rows, cols, 0, 0))

    def read(self, timeout):
        end = time.time() + timeout
        while time.time() < end:
            r, _, _ = select.select([self.fd], [], [], 0.1)
            if r:
                try:
                    data = os.read(self.fd, 4096)
                except OSError:
                    return
                if not data:
                    return
                self.buf += data

    def plain(self):
        """what was drawn since mark(), with the escape sequences removed"""
        return CSI.sub("", self.buf[self.pos:].decode("utf-8", "replace"))

    def expect(self, text, timeout=10):
        end = time.time() + timeout
        while time.time() < end:
            if text in self.plain():
                return True
            self.read(0.2)
        return False

    def send(self, s):
        os.write(self.fd, s.encode())
        time.sleep(0.3)

    def mark(self):
        self.pos = len(self.buf)

    def close(self):
        try:
            os.close(self.fd)
        except OSError:
            pass
        try:
            os.kill(self.pid, 15)
        except OSError:
            pass
        try:
            os.waitpid(self.pid, 0)
        except OSError:
            pass


def main():
    newsboat = shutil.which("newsboat")
    if not newsboat:
        print("newsboat_pty: newsboat is not installed here -- skipped "
              "(apt-get install newsboat / brew install newsboat)")
        return 0
    fail = 0

    def ok(cond, what, extra=""):
        nonlocal fail
        print("  %s %s%s" % ("ok  " if cond else "FAIL", what, ("   " + extra) if extra and not cond else ""))
        if not cond:
            fail += 1

    with tempfile.TemporaryDirectory(prefix="spark-newsboat-") as tmp:
        work, bindir = [os.path.join(tmp, d) for d in ("work", "bin")]
        os.makedirs(work)
        os.makedirs(bindir)
        # the README's install lines, performed: the snippet appended to
        # a fresh config, the wrapper on PATH as shipped (no chmod here
        # -- the repo file must already be executable)
        with open(os.path.join(REPO, "config.spark")) as f:
            snippet = f.read()
        config = os.path.join(tmp, "config")
        with open(config, "a") as f:
            f.write(snippet)
        os.symlink(os.path.join(REPO, "spark-newsboat"),
                   os.path.join(bindir, "spark-newsboat"))
        stub = os.path.join(bindir, "spark")
        with open(stub, "w") as f:
            f.write(STUB)
        os.chmod(stub, 0o755)
        log = os.path.join(tmp, "stub.log")
        feed = os.path.join(work, "feed.xml")
        with open(feed, "w") as f:
            f.write(FEED)
        stubfeed = os.path.join(work, "stubfeed.xml")
        with open(stubfeed, "w") as f:
            f.write(STUBFEED)
        urls = os.path.join(tmp, "urls")
        with open(urls, "w") as f:
            f.write("file://%s\n" % feed)
        urls2 = os.path.join(tmp, "urls2")
        with open(urls2, "w") as f:
            f.write("file://%s\n" % stubfeed)
        cache = os.path.join(tmp, "cache.db")
        env = {"HOME": tmp, "TERM": "xterm", "PATH": bindir + ":" + os.environ.get("PATH", "/usr/bin:/bin"),
               "LANG": "C.UTF-8", "LC_ALL": "C.UTF-8", "STUB_LOG": log}
        argv = [newsboat, "-u", urls, "-c", cache, "-C", config, "-r"]

        def logged():
            try:
                with open(log) as f:
                    return f.read()
            except OSError:
                return ""

        def fresh(open_article=True):
            for p in (log, log + ".stdin", cache, cache + ".lock"):
                if os.path.exists(p):
                    os.unlink(p)
            b = Reader(argv, env, work)
            ok(b.expect("probe feed"), "newsboat draws the feed list")
            b.send("\r")
            b.expect("gate article")
            if open_article:
                b.send("\r")
                ok(b.expect("gate opens at nine"), "the article opens")
            b.mark()
            return b

        # A. ,s in the article: the title, the prompt, Enter = overview;
        # the article travels with its header and no path; newsboat is
        # navigable after the exchange
        b = fresh()
        b.send(",s")
        ok(b.expect("chat>"), "the macro opens the spark prompt", b.plain()[-200:])
        ok("the gate article" in b.plain() and "probe feed" in b.plain() and "----" in b.plain(),
           "the card stands above the prompt: title, meta line, a rule", b.plain()[-300:])
        ok(b.expect("hello"), "the room says hello before the first prompt", b.plain()[-200:])
        b.send("\r")
        ok(b.expect("reading") and b.expect("characters"),
           "the first wait reads the article, and says so", b.plain()[-200:])
        ok(b.expect("STUB-READ"), "Enter alone is the overview: the answer shows", b.plain()[-300:])
        got = logged()
        ok(got.strip() == "read", "spark read got no words -- the overview, no name, no path", got)
        with open(log + ".stdin") as f:
            stdin = f.read()
        ok("Title: the gate article" in stdin and "gate opens at nine" in stdin,
           "the rendered article travelled on stdin, header and text", repr(stdin[:150]))
        ok(tmp not in stdin and "feed.xml" not in stdin, "no path reaches spark", repr(stdin[:150]))
        b.read(0.5)
        b.mark()
        b.send("\r")            # empty prompt after an answer: return
        b.send("q")             # article -> article list: newsboat repaints
        ok(b.expect("gate article"), "newsboat is alive and repaints after the exchange", b.plain()[-200:])
        b.close()

        # B. words at the prompt are the CONVERSATION: spark edit ? with
        # a thread and the article's name; globs stay literal
        b = fresh()
        b.send(",s")
        b.expect("chat>")
        b.send("does it name a *price*\r")
        b.expect("STUB-EDIT")
        got = logged().strip()
        ok(got.startswith("edit ? does it name a *price* --thread nb-")
           and "--about a published article" in got and "--name the gate article" in got,
           "the words run spark edit ? with thread, about and name", got)
        b.send("\r")
        b.close()

        # C. the editors' habit: a leading ? is stripped (one ?, not two)
        b = fresh()
        b.send(",s")
        b.expect("chat>")
        b.send("?does it name a price\r")
        b.expect("STUB-EDIT")
        ok(logged().strip().startswith("edit ? does it name a price --thread nb-"),
           "a leading ? is stripped, the editors' habit", logged())
        b.send("\r")
        b.close()

        # E. a refusal on spark's stderr shows on screen
        b = fresh()
        b.send(",s")
        b.expect("chat>")
        b.send("fail\r")
        ok(b.expect("STUB-OPENING"), "a refusal shows where the answer would be", b.plain()[-300:])
        b.send("\r")
        b.close()

        # F. Ctrl-C at the prompt runs nothing; newsboat comes back
        b = fresh()
        b.send(",s")
        b.expect("chat>")
        b.send("\x03")
        time.sleep(0.6)
        ok(not os.path.exists(log), "Ctrl-C at the prompt runs nothing")
        b.mark()
        b.send("q")
        ok(b.expect("gate article"), "newsboat comes straight back after the cancel", b.plain()[-200:])
        b.close()

        # F2. a follow-up rides the SAME thread: the conversation law's whole
        # point -- "can you translate that?" has a that
        b = fresh()
        b.send(",s")
        b.expect("chat>")
        b.send("first question\r")
        b.expect("STUB-EDIT")
        b.send("second question\r")
        ok(b.expect("thinking", 15), "a follow-up's wait is thinking, not re-reading")
        b.expect("STUB-EDIT", 15)
        lines = logged().strip().split("\n")
        def tid(l):
            w = l.split()
            return w[w.index("--thread") + 1] if "--thread" in w else "?" + l
        ok(len(lines) == 2 and lines[0].startswith("edit ? first question")
           and lines[1].startswith("edit ? second question")
           and tid(lines[0]) == tid(lines[1]),
           "the follow-up rides the same thread", logged())
        b.send("\r")
        b.close()

        # F3. a stub article says so instead of refusing; Enter returns
        # (its own instance, its own single feed: no list navigation)
        if os.path.exists(log):
            os.unlink(log)
        b = Reader([newsboat, "-u", urls2, "-c", os.path.join(tmp, "cache2.db"),
                    "-C", config, "-r"], env, work)
        ok(b.expect("stub feed"), "the stub feed draws")
        b.send("\r")
        b.expect("link only")
        b.send("\r")            # open the stub article
        b.expect("Comments")
        b.mark()
        b.send(",s")
        ok(b.expect("only a stub"), "a stub is named, not sent", b.plain()[-300:])
        b.send("\r")            # Enter on a stub: nothing to overview, return
        time.sleep(0.6)
        ok(not os.path.exists(log), "nothing was sent for the stub")
        b.mark()
        b.send("q")
        ok(b.expect("link only"), "newsboat is back after the stub visit", b.plain()[-200:])
        b.close()

        # F4. the quit grammar: q (the family's close key) returns to
        # newsboat from a FRESH session too, and never reaches the model
        b = fresh()
        b.send(",s")
        b.expect("chat>")
        b.mark()
        b.send("q\r")
        time.sleep(0.8)
        ok(not os.path.exists(log), "q at the prompt runs nothing")
        b.send("q")
        ok(b.expect("gate article"), "q returns to newsboat, fresh session or not", b.plain()[-200:])
        b.close()

        # G. ,s from the article LIST pipes the selected article too
        b = fresh(open_article=False)
        b.send(",s")
        ok(b.expect("chat>"), "the macro works from the article list")
        b.send("\r")
        b.expect("STUB-READ")
        with open(log + ".stdin") as f:
            stdin = f.read()
        ok("Title: the gate article" in stdin, "the selected article travelled", repr(stdin[:150]))
        b.send("\r")
        b.close()

        # H. from a plain shell the wrapper takes the words directly
        if os.path.exists(log):
            os.unlink(log)
        p = subprocess.run([os.path.join(bindir, "spark-newsboat"), "the", "words"],
                           input="Title: t\n\nbody\n", capture_output=True, text=True, env=env)
        ok(p.returncode == 0 and "STUB-READ" in p.stdout,
           "pipe mode answers on stdout", p.stdout + p.stderr)
        ok(logged().strip() == "read the words", "pipe mode passes the words", logged())

        # the wrapper never wrote into the repo
        ok(not os.path.exists(os.path.join(REPO, "stub.log")), "the repo tree is untouched")

    print("newsboat_pty: %s" % ("all ok" if fail == 0 else "%d FAILED" % fail))
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
