# reconstructor-macos

Remote Mac worker (#23). It pulls `reconstruct` tasks from the API, so the Mac needs no inbound
connection, runs Apple Object Capture through a small Swift CLI and uploads the model.

```text
scan3d-reconstructor (Python)  --claims-->  API  (worker token, fenced lease)
   |-- downloads photos, runs scan3d_pipeline.preflight (blocks on flagged photos)
   |-- runs scan3d-object-capture <photos> <out.usdz> --detail full   (Swift, PhotogrammetrySession)
   `-- uploads model.usdz (kind "reconstruction", parent = first photo), completes the task
```

## Run

```sh
cd object-capture-cli && swift build -c release        # needs macOS 13+, Apple Silicon recommended
export SCAN3D_API_URL=https://<host> SCAN3D_WORKER_TOKEN=<worker token>
export SCAN3D_OBJECT_CAPTURE_BIN=$PWD/object-capture-cli/.build/release/scan3d-object-capture
uv run scan3d-reconstructor
```

Mint the worker token with `POST /api/tokens {"kind": "worker"}` as a logged-in user.

## Task payload

```json
{"photos": [{"artifact_id": "...", "filename": "IMG_1.jpg"}], "detail": "full", "skip_preflight": false}
```

`skip_preflight` is the explicit user override after reviewing flagged photos.

## Manual checks (not automatable here)

- Run on a real Apple Silicon Mac with an ordinary phone photo set of a measured object. Record
  macOS version, chip, RAM, photo count, wall time and peak memory.
- Measure the output against the object. Sensor-scale metadata is evidence, not proof of accuracy.
- Confirm cancel (task cancel while running) stops the CLI and leaves no partial artifact.
- The USDZ is not ingested yet: ingest (#9) is not implemented.
