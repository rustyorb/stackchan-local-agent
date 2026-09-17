# PR #2 review findings, 2026-09-17

Reviewed Sourcery's five inline findings on commit `9647f28612b1765b150fc11c4e4b6ee94eb59d80`. The push succeeded and GitHub reports the open PR as mergeable. The workflow-run API returned no pull-request-triggered Actions runs for that commit; these findings came from the review bot, not a reproduced build failure.

## Missing server.auth_key: not a startup defect in the configured entry point

The reviewer correctly identified unconditional reads in the WebSocket and OTA constructors, but missed the initialization before them. The Docker image runs `python app.py`. At pinned server revision `6afc54a17def47578a4b3efc4680873689d3168b`, `app.py:53–62` reads an optional key, falls back to the manager secret, then generates a UUID key if both are absent. It stores the key before constructing `WebSocketServer` and `SimpleHttpServer`.

`tests/test_upstream_startup.py` executes that exact upstream `main()` and the actual WebSocket, HTTP, and OTA constructors with model initialization, sockets, logging, and other external work substituted. It starts with the generated standalone configuration lacking `auth_key` and confirms the same generated key reaches both authentication managers. This is a focused initialization regression, not a full Docker/server smoke test. Directly instantiating those constructors without the entry point's initialization is not supported by this deployment.

## subprocess.run: no shell-injection defect demonstrated

`firmware/build_factory.py` passes a list of arguments and never enables `shell=True`. Executables are selected by the helper's own calls; the endpoint host is validated as a private IPv4 address and the port as an integer range. Applying shell escaping to individual argv elements would alter their values and can break paths on Windows. The audit finding does not establish shell command injection here. Build tools and downloaded source still execute code as part of an explicitly requested build.

## Three ws:// findings: genuine transport limitation, still open

The three findings refer to the same design in the renderer, build helper, and documentation. The current first-device integration uses plain WebSocket with authentication disabled on a trusted private LAN. Audio and messages have no application-layer encryption; reachable LAN peers can attempt sessions. Using a private address alone does not authenticate the robot or server.

These warnings are **not fixed or suppressed**. A real fix needs TLS termination, certificate trust on the ESP32, and coordinated device authentication. Merely changing `ws://` to `wss://` would break connectivity because the current listener does not serve TLS. Keep this build on a trusted, isolated bench network while physical integration is validated. Do not describe it as suitable for an untrusted LAN or public deployment.

No review thread was dismissed, no merge was performed, and no hardware-validation claim follows from these checks.
