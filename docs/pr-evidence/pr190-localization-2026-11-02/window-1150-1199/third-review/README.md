# ChaptarrNG PR #190 W1150–W1199 blind third review

This is an independent machine semantic review of 138 cells at PR head 6e7a5341b7ccac31d950c73db68277f9a1f18f8e, tree d073e1373021bf715db37461a12654f7e993cdbf. It is not native-speaker approval.

## Inputs and verification

- Source-only packet: /mnt/disks/scratch/task-scratch/chaptarrng-pr190-window-1150-1199-third-review-20261103/source-only-review-input.jsonl
- Packet SHA256: e578c2b2afa22028d0cf4a0b2a39b05013bb463d697510656a5d0ab01e87104a
- The packet SHA256SUMS was verified before opening the packet.
- English source and current target cells, localization file hashes, and pinned caller files/lines were independently matched against the clean checkout at the exact head and tree.
- The review used the source-only packet and repository source. Prior review ledgers, comparison diffs, and proposed targets/dispositions were not opened.

## Results

- Rows reviewed: 138
- accept-current: 37
- correction/refinement: 101
- Every row records an effective target, a rationale, caller-sensitive note, and confidence.
- Every row records placeholder counts, ICU and markup review, protected literals, and protocol/API literal review. The input rows contain no ICU patterns or markup. Placeholder and literal checks passed for all rows.
- Technical/API names including M4B, m4b-tool, FFmpeg, FFprobe, Direct, bookId, authorId, seriesId, and URLs were checked for exact preservation where present.
- Dynamic tokens remain exact and in the expected counts. Protocol labels, paths, exit codes, durations, and client summaries remain dynamic when supplied through placeholders.

## Ledger fields

Each JSONL record includes its review key, locale, source/target pins, current and effective targets, disposition, rationale, verified caller references, placeholder/ICU/markup/literal results, confidence, and native_speaker_approval: false. For accepted rows, proposed_final_target is null; for corrections/refinements it contains the proposed text.

## Scope

No repository files were edited. No build, test, scan, package, CI, browser, or GitHub action was run. Only independent review artifacts in this directory were created.

See exact-head-attestation.json for pre/post checkout status and SHA256SUMS for output checksums.
