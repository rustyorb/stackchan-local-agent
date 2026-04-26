# Firmware Patch Notes

`xiaozhi-esp32.patch` captures local changes inside `U:\_Projects\StackChan\firmware\xiaozhi-esp32`, which is an ignored nested checkout.

Current local firmware state also depends on this ignored `sdkconfig` setting:

```text
# CONFIG_USE_AUDIO_PROCESSOR is not set
```

That setting bypasses the ESP AFE path while debugging CoreS3 microphone capture.
