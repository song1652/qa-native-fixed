# Import Studio test fixtures

`workbooks.json` is the source of truth for isolated Import Studio tests. Tests
materialize these rows as `.xlsx` files under a temporary project root, so they
never read or write the repository's `import/` or `testcases/` directories.

The fixture intentionally contains:

- two workbooks;
- two sheets per workbook;
- different column names in the second workbook;
- six unique test cases across four target groups.
