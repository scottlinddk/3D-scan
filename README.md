# 3d-scan

Scan a physical object and get a **print-ready 3MF** for **Bambu Studio** (Bambu Lab printers).

Inspired by [wesbos/3d-model-anything](https://github.com/wesbos/3d-model-anything), which scans rooms into Three.js scenes. This project applies the same "capture the evidence, then reconstruct" idea to objects, with printability as the goal: watertight, manifold, correctly scaled in mm, flat on the bed, and within the printer's build volume.

## How it will work

1. **Capture** with an existing scanner app (Polycam, Scaniverse, Reality Composer), a photo set, or later a native iOS app.
2. **Upload** to the local web app.
3. **Pipeline:** ingest, clean, repair, scale, orient, decimate, validate.
4. **Review** in the 3D viewer, fix orientation or scale if needed.
5. **Export** 3MF (and STL) and open it in Bambu Studio.

## Status

Planning. See:
- [Architecture](docs/ARCHITECTURE.md)
- [Implementation plan](docs/IMPLEMENTATION_PLAN.md)
- [Issues](https://github.com/scottlinddk/3d-scan/issues) for the task breakdown
