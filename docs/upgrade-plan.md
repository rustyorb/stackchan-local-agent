# Stakia upgrade plan

The complete original research and upgrade plan is preserved in this repository on the [research documentation branch](https://github.com/rustyorb/stackchan-local-agent/blob/docs/stakia-research-plan/docs/upgrade-plan.md).

The long research document is separate to keep automated reviews within their size limit. The host runtime is reviewed on `codex/stakia-host-runtime`; PR #2 adds the firmware on top. The complete upgrade remains on `codex/stakia-upgrade`. No executable changes or security tests are excluded from review.

For the current implementation, use:

- [Host setup](../README.md)
- [Firmware build](../firmware/STAKIA-BUILD.md)
- [Implementation status](implementation-status.md)
- [Security review resolution](pr-2-review.md)

The current design uses authenticated TLS, a locally generated CA, a private robot credential, and a localhost-only dashboard. Earlier plaintext or vendor-bootstrap proposals in the research are superseded.
