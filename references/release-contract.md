# Release contract

A stable installation consumes `release-manifest.json` with:

- `schemaVersion: 1`;
- a non-empty `releaseId` and `hardwareProfileId`;
- `chipFamily: ESP32-S3` for the first profile;
- `acceptance.status: allowed` and a non-empty acceptance report ID;
- `flash.eraseAll: false`;
- one or more files with a unique role, non-negative address, positive size, relative in-package path, and SHA-256;
- no overlapping Flash ranges.

The installer verifies every artifact's actual size and SHA-256 before creating a write plan. A candidate, revoked, malformed, incomplete, path-traversing, overlapping, missing, or changed release is blocked.

The Manifest is the only source of Flash addresses. Examples, prose documentation, Agent memory, and filenames are not address authorities.

## Candidate hardware acceptance

A candidate keeps `acceptance.status: candidate` and a null `reportId`. It is
never accepted by `release verify`, `flash plan`, or `flash apply`.

Hardware-development testing uses the separate `flash candidate-plan` and
`flash candidate-apply` commands. Candidate apply requires exact confirmation
of both the Release ID and hardware Profile ID. This path is only for an
identified development board during acceptance work; it does not make the
Release stable or expand the public host support matrix.
