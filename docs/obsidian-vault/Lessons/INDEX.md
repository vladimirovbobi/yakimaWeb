# Lessons learned

Things we discovered the hard way. Each entry links to the sprint where it
came up. The format is `Lesson · Why · How to apply next time`.

## Sprint 0–1

- **Don't trust pre-existing audit claims.** The first audit said `/guidelines`,
  `/privacy`, `/terms`, `/videos` were stub pages — they weren't. Rule:
  `Read` the file before assuming.
- **The 1301-2nd-street reference uses the exact same tokens as `vrov-new`.**
  Color drift audits should be near-instant. We over-budgeted for it.

## Sprint 1.5

- **JPEG `quality="keep"` is the single most important Pillow flag for true
  lossless re-encode.** Combined with `optimize=True`, you preserve quantization
  tables byte-for-byte. Document this prominently — easy to miss.
- **DRF `permission_classes = [...]` triggers RUF012.** Add to ignore list once;
  don't fight per-class.

## Sprint 2

- See [[sprint-2-audit]] when written.

## Sprint 6

- See [[sprint-6-delivery]] when written.

## Sprint 7

- See [[sprint-7-bff]] when written.
