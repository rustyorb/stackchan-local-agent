# PR #2 review resolution, 2026-09-17

The security warnings were real check failures. Passing local unit tests did not make Sourcery's check pass. This update addresses the transport design and adds reproducible GitHub regression checks.

## Transport and authentication

The standalone service now terminates TLS itself and requires a random 256-bit robot credential before accepting a WebSocket upgrade. The firmware sends that credential and validates the server through a local CA bundle. Missing certificates or credentials stop startup. There is no plaintext or anonymous fallback and no device-ID authentication bypass.

The private CA and server certificate are generated on the PC without external services. Only the public CA is embedded as a trust root. The server key and robot credential are ignored by Git, reused across runs, and never printed. Generated firmware contains the robot credential and must not be shared. See the README for rotation and certificate renewal.

Connection logging omits request headers so the bearer credential does not appear in normal server logs. Generated configuration and firmware headers are atomically written with private file permissions.

The unused HTTP listener is disabled, Docker publishes only the secure voice port on the chosen LAN address, and the dashboard binds to localhost. Optional container-to-host bridge integrations remain disabled until separately secured. The firmware uses its RTC, with build time as a floor after RTC loss, for certificate validity checks.

## Subprocess audit finding

The native build helper permits only Git and its own Python interpreter, passes an argument vector, and explicitly disables shell evaluation. A regression executes shell metacharacters as literal arguments and rejects other executables. The existing audit false positive has a narrowly scoped inline suppression with its reasoning; the rule is not disabled across the repository.

## Startup-key finding

The pinned upstream entry point creates its internal authentication-manager key before constructing WebSocket and HTTP handlers. The earlier startup regression exercises that ordering. This finding was not a reproduced startup crash.

## Verification scope

Real socket tests exercise TLS trust, hostname matching, credential rejection, successful authenticated data exchange, and the patched production WebSocket listener. Speech models and logging are substituted in the upstream listener test; socket/TLS/protocol handling is real. Firmware checks validate patch application, endpoint generation, verification settings, and eye geometry. Full ESP-IDF compilation, the complete Docker image, and physical robot behavior remain bench checks. GitHub check results must be read separately after this update is pushed; this document does not claim they have passed.
