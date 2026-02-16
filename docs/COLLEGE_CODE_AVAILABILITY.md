# College Code Availability Notes

## Scope
- Source: `https://web-as.tamu.edu/gradereports/`
- Report type: Grade Distribution PDFs
- Term tested: `Fall 2023` (`term key = 20233`)
- Validation method: direct PDF URL probing (`grd{term}{code}.pdf`)

## Key Finding
Not all codes shown in the dropdown are expected to have downloadable files for each term.  
For Fall 2023 specifically, several legacy codes return `HTTP 404`.

## Confirmed Fall 2023 Working Codes
- `AC`
- `AE`
- `AG`
- `AP`
- `AT`
- `BA`
- `DT`
- `DT_PROF`
- `EH`
- `EN`
- `GB`
- `GV`
- `MN`
- `MS`
- `NS`
- `PH`
- `PM_PROF`
- `QT`
- `SL`
- `SL_PROF`
- `VF`
- `VT`
- `VT_PROF`

## Confirmed Fall 2023 404 Codes
- `AD`
- `AR`
- `CP_PROF`
- `DN`
- `DN_PROF`
- `ED`
- `GE`
- `LA`
- `MD`
- `MD_PROF`
- `MN_PROF`
- `SC`
- `UT`
- `VM`
- `VM_PROF`

## Practical Mapping Notes
- `GE`, `LA`, `SC` are labeled `Pre-Fall 2022` on the source page.
  - For post-Fall-2022 data, use `AT` where applicable.
- Several `College` variants appear replaced by `School` variants in modern terms:
  - `AR` -> `AC`
  - `ED` -> `EH`
  - `DN`/`DN_PROF` -> `DT`/`DT_PROF`
  - `MD`/`MD_PROF` -> `MN`/`MN_PROF` (note: `MN_PROF` still 404 in Fall 2023 tests)
  - `CP_PROF` -> `PM_PROF`
  - `VM`/`VM_PROF` -> `VT`/`VT_PROF`

## Operational Guidance
- Treat `HTTP 404` on these legacy codes as expected source availability behavior, not parser failure.
- For semester refreshes, re-validate codes at runtime before bulk download attempts.
