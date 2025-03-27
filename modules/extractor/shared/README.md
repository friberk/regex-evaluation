
# shared

Provides shared utilities by all packages. Some things it provides:
- models for all types (regex entity, package spec, etc.)
- A RAII directory guard. Wrap a directory in `CleanUpRepoGuard` to (optionally) delete the directory held when it goes out of scope.
- Tool for running cloc
- Tools for traversing directories to find files. For example, we have a JS file traverser to pull out all JS files from a project.
