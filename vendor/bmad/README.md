# BMAD-METHOD (Vendored)

This directory contains a vendored copy of BMAD-METHOD (MIT License) for integration into the Cerebral platform.

## Source
- **Repository**: https://github.com/bmadcode/BMAD-METHOD
- **License**: MIT License
- **Copyright**: Copyright (c) 2025 BMad Code, LLC

## Integration Notes
- This is a headless integration - no web UI components are enabled
- Core agent functionality is preserved for PRD/Architecture/Story generation
- Integration points are documented in `docs/architecture/bmad_api_inventory.md`

## Upstream Sync Policy
- Monthly upstream sync procedure documented in `docs/engineering/bmad_upstream_sync.md`
- Contract tests ensure API compatibility before merge
- Breaking changes are detected and handled via automated testing

## Structure
- `bmad-core/`: Core agent functionality and workflows
- `docs/`: Original BMAD documentation
- `tools/`: BMAD tooling and utilities
- `expansion-packs/`: Additional BMAD capabilities

## Usage
BMAD agents are accessed via the Cerebral platform API facade:
- POST `/bmad/planning/prd`
- POST `/bmad/planning/architecture` 
- POST `/bmad/planning/story`
- POST `/bmad/gates/approve`