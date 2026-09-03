# ESP32Marauder Feberis release automation

Files to place in the `ESP32Marauder-builds` repository:

```text
.github/workflows/upstream-build.yml
.github/workflows/publish-tested.yml
scripts/patch_configs.py
```

## What it does

1. `upstream-build.yml` runs once per day at 03:17 UTC and checks the latest stable GitHub release of `justcallmekoko/ESP32Marauder`.
2. If the corresponding final release or test candidate does not already exist in this repository, it checks out the exact upstream tag and commit.
3. `scripts/patch_configs.py` adds the two BPM Circuits targets to upstream `esp32_marauder/configs.h`:
   - `BPMCIRCUITS_FEBERIS` -> Feberis, NeoPixel, no GPS.
   - `BPMCIRCUITS_FEBERIS_PRO` -> Feberis Pro, NeoPixel + GPS UART1, TX GPIO14, RX GPIO13.
4. GitHub Actions builds both variants using the same Arduino core/tooling pattern currently used by upstream ESP32Marauder (`esp32:esp32:d32:PartitionScheme=min_spiffs`, ESP32 core 3.3.4, NimBLE 2.3.8).
5. The workflow creates `test-<upstream tag>` as a GitHub prerelease in `ESP32Marauder-builds`, containing both `.bin` files plus `SHA256SUMS.txt` and `BUILD_INFO.txt`.
6. After hardware verification, manually run `Publish tested Feberis release`, entering the upstream version/tag (for example `v1.15.1`).
7. `publish-tested.yml` downloads the exact prerelease assets, verifies their SHA-256 checksums and publishes those same files as the final release. It does not compile firmware again.

## Manual build

`Actions -> Build Feberis from upstream release -> Run workflow`

- Leave `upstream_tag` empty to use the latest stable upstream release.
- Set a tag such as `v1.15.1` to build that exact upstream release.
- Set `force=true` only to replace an existing `test-<tag>` prerelease. A final release is never overwritten automatically.

## Final publication

`Actions -> Publish tested Feberis release -> Run workflow`

- `version`: upstream tag that was tested, e.g. `v1.15.1`.
- `delete_candidate`: optionally delete the test prerelease after the final release is created.

No PAT is required when the workflows live in the same `ESP32Marauder-builds` repository; they use the repository `GITHUB_TOKEN` with the permissions declared in the workflows.
