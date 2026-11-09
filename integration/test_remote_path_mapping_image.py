#!/usr/bin/env python3
"""Disposable HTTP + SQLite regression proof for ChaptarrNG issue #199.

Requires Docker and a fully built ChaptarrNG image. Does not access any
production databases, download clients, network shares or credentials.
"""
import argparse
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from xml.etree import ElementTree


def docker(*args, check=True):
    return subprocess.run(["docker", *map(str, args)], text=True,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          check=check)


def api(base, key, method, path, body=None):
    headers = {"Accept": "application/json", "X-Api-Key": key,
               "X-ChaptarrNG-Client": "native"}
    data = None
    if body is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(body).encode()
    req = Request(base + path, headers=headers, data=data, method=method)
    try:
        with urlopen(req, timeout=20) as response:  # nosemgrep: python.lang.security.audit.dynamic-urllib-use-detected.dynamic-urllib-use-detected -- task-owned loopback API
            raw = response.read().decode()
            return response.status, response.headers, json.loads(raw) if raw else None
    except HTTPError as error:
        details = error.read().decode(errors="replace")
        raise AssertionError(f"{method} {path}: HTTP {error.code}: {details[:1200]}") from error


def ready(base, config, timeout):
    deadline = time.monotonic() + timeout
    last_error = ""
    while time.monotonic() < deadline:
        if config.is_file():
            try:
                key = ElementTree.parse(config).findtext("ApiKey")  # nosemgrep: python.lang.security.use-defused-xml-parse.use-defused-xml-parse -- generated local config.xml only
                if key:
                    with urlopen(base + "/ping", timeout=3) as response:  # nosemgrep: python.lang.security.audit.dynamic-urllib-use-detected.dynamic-urllib-use-detected -- task-owned loopback health
                        if response.status == 200:
                            return key
            except (ElementTree.ParseError, OSError, URLError, TimeoutError) as error:
                last_error = str(error)
        time.sleep(2)
    raise AssertionError(f"Chaptarr never became ready: {last_error}")


def persisted(db_file, ident, host):
    assert db_file.is_file(), f"SQLite DB missing: {db_file}"
    with sqlite3.connect(f"file:{db_file}?mode=ro", uri=True) as db:
        row = db.execute(
            'SELECT "Host", "RemotePath", "LocalPath" FROM "RemotePathMappings" WHERE "Id" = ?',
            (ident,),
        ).fetchone()
    assert row is not None, f"Mapping ID {ident} absent from SQLite"
    assert row[0].lower() == host.lower(), row
    assert "BookshelfDownloads" in row[1], row
    assert row[2].rstrip("/") == "/downloads", row


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image", required=True)
    parser.add_argument("--port", type=int, default=18789)
    parser.add_argument("--ready-timeout", type=int, default=240)
    args = parser.parse_args()
    container = f"chaptarr-rpm-proof-{os.getpid()}"
    base = f"http://127.0.0.1:{args.port}"

    with tempfile.TemporaryDirectory(prefix="chaptarr-rpm-199-") as directory:
        config = Path(directory) / "config"
        downloads = Path(directory) / "downloads"
        config.mkdir()
        downloads.mkdir()
        config.chmod(0o777)
        downloads.chmod(0o777)
        try:
            run = docker("run", "-d", "--name", container,
                         "-p", f"127.0.0.1:{args.port}:8789",
                         "-v", f"{config}:/config",
                         "-v", f"{downloads}:/downloads",
                         "-e", f"PUID={os.getuid()}", "-e", f"PGID={os.getgid()}",
                         args.image)
            print(f"Started disposable container: {run.stdout.strip()}", flush=True)
            key = ready(base, config / "config.xml", args.ready_timeout)
            root = "/api/v1/remotepathmapping"
            host = "synthetic-download-node"
            remote = "\\\\synthetic-server\\share\\BookshelfDownloads\\"
            body = {"downloadClientId": 0, "host": host,
                    "remotePath": remote, "localPath": "/downloads/"}

            code, _, tested = api(base, key, "POST", root + "/test", body)
            assert code == 200 and isinstance(tested, dict), tested
            assert tested.get("host") == host, tested
            assert "BookshelfDownloads" in (tested.get("remotePath") or ""), tested
            assert (tested.get("localPath") or "").rstrip("/") == "/downloads", tested
            assert (tested.get("mappedPath") or "").rstrip("/") == "/downloads", tested
            assert tested.get("isMapped") is True, tested
            assert tested.get("localPathExists") is True, tested
            assert tested.get("localPathWritable") is True, tested
            print("PASS: test endpoint retained request and mapped UNC to /downloads", flush=True)

            code, headers, created = api(base, key, "POST", root, body)
            assert code == 201 and isinstance(created, dict), created
            ident = created.get("id")
            assert isinstance(ident, int) and ident > 0, (
                f"POST returned no saved ID: {created!r}; Location={headers.get('Location')!r}")
            assert headers.get("Location", "").rstrip("/").endswith(f"/{ident}"), headers
            print(f"PASS: POST created real mapping ID {ident}", flush=True)

            code, _, entries = api(base, key, "GET", root)
            assert code == 200 and isinstance(entries, list), entries
            assert any(x.get("id") == ident for x in entries), entries
            code, _, entry = api(base, key, "GET", root + f"/{ident}")
            assert code == 200 and entry.get("id") == ident, entry
            persisted(config / "chaptarr.db", ident, host)
            print("PASS: list, read by ID and actual SQLite row", flush=True)

            docker("restart", container)
            key = ready(base, config / "config.xml", args.ready_timeout)
            code, _, entries = api(base, key, "GET", root)
            assert code == 200 and any(x.get("id") == ident for x in entries), entries
            persisted(config / "chaptarr.db", ident, host)
            print("PASS: mapping survives Docker restart", flush=True)

            code, _, _ = api(base, key, "DELETE", root + f"/{ident}")
            assert code in (200, 202, 204), code
            _, _, entries = api(base, key, "GET", root)
            assert not any(x.get("id") == ident for x in entries), entries
            print("PASS: DELETE removes mapping", flush=True)
            print("SUCCESS: ChaptarrNG remote mapping HTTP+SQLite lifecycle", flush=True)
        except Exception:
            logs = docker("logs", "--tail", "120", container, check=False)
            print("===== container logs =====", file=sys.stderr)
            print((logs.stdout + logs.stderr)[-14000:], file=sys.stderr)
            raise
        finally:
            docker("rm", "-f", container, check=False)


if __name__ == "__main__":
    main()
