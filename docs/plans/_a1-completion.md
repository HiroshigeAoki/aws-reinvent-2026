# A1 completion report

- **task:** A1 (`title` 必須化 / TDD)
- **changed files:**
  - `/home/aoki/dev/aws-reinvent-2026/tests/test_reinvent.py`
  - `/home/aoki/dev/aws-reinvent-2026/scripts/reinvent.py`

## Red evidence (before implement)

New title-schema tests failed against the old `title_ja`-required implementation:

```
FAIL: test_empty_or_whitespace_title_is_rejected ... AssertionError: False is not true
FAIL: test_missing_title_is_rejected ... AssertionError: False is not true
FAIL: test_title_ja_may_be_omitted
  AssertionError: Lists differ: ['sessions[0].title_ja: 必須項目です', ...] != []
FAIL: test_catalog_table_uses_english_title
  AssertionError: '[Designing Agents](...)' not found (table still used title_ja)
FAIL: test_render_h1_uses_english_title
  AssertionError: '# A101: Designing Agents' not found (H1 was Japanese)
FAIL: test_render_includes_title_ja_helper_line
  AssertionError: helper line after H1 missing title_ja

Ran 25 tests in 0.006s
FAILED (failures=8)
```

## Green evidence (after implement)

```
test_bad_core_types_produce_errors ... ok
test_duplicate_is_scoped_to_year_and_id ... ok
test_empty_or_whitespace_title_is_rejected ... ok
test_empty_title_ja_is_rejected_when_present ... ok
test_missing_title_is_rejected ... ok
test_naive_datetime_wrong_year_and_reversed_times_are_rejected ... ok
test_path_traversal_and_non_ascii_ids_are_rejected ... ok
test_source_urls_reject_credentials_and_non_https ... ok
test_title_ja_may_be_omitted ... ok
test_unknown_end_is_allowed_without_guessing_duration ... ok
test_valid_and_previous_year_entries ... ok
test_catalog_table_uses_english_title ... ok
test_deterministic_render_preserves_notes_and_input ... ok
test_handwritten_target_is_not_overwritten ... ok
test_output_symlink_cannot_escape_root ... ok
test_render_h1_uses_english_title ... ok
test_render_includes_title_ja_helper_line ... ok
test_search_matches_topics_case_insensitively ... ok
test_search_prefers_english_title_in_results ... ok
test_candidates_do_not_conflict_and_incomplete_times_warn ... ok
test_exact_transfer_boundary_is_allowed ... ok
test_nested_overlaps_are_all_found ... ok
test_offsets_are_compared_as_instants ... ok
test_transfer_gap_and_same_venue ... ok
test_unknown_session_invalid_status_and_duplicates_fail ... ok

----------------------------------------------------------------------
Ran 25 tests in 0.005s

OK
```

Command: `python3 -m unittest discover -s tests -v` (cwd: `/home/aoki/dev/aws-reinvent-2026`)

## Open items

- `data/catalog.json` still lacks English `title` on sessions; real `validate` / `render` against the live catalog will fail until **Task A2**.
- A1 intentionally did not modify `catalog.json`.
