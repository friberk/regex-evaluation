
# Useful One-Liners

These are some bash one-liners that I use frequently:

### Split package specs into a fixed number of chunks
```bash
$ split --numeric-suffixes -n l/<chunks> <package-spec-file> pkg-specs-
```

`chunks` is how many files you want to make. The `l/` part ensures that you split on
lines, not characters (very important for ndjson)

### Split package specs into files with fixed line count
```bash
$ split -a <suffix_length> --numeric-suffixes -l <line_count> <package-spec-file> pkg-specs-
```
Like above, but you choose lines instead of files. You might have to provide a fairly long
suffix length depending on the size of the file.

### Delete all the files you create in `/tmp`

```bash
$ find . -user anonymous -maxdepth 1 -exec rm -rf {} +
```
