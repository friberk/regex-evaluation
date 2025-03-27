use std::path::Path;
use walkdir::{DirEntry, WalkDir};
use log::trace;
use crate::traverser::filter::{DirectoryEntryFilter, DirectoryEntryFilterChain, IncludeFileExtensionFilter, IgnoreSpecialFileExtensions, PathNotContainsSegment, SkipFilenameFilter, SkipHiddenPathsFilter, SkipNonFileOrDirectoryFilter};

pub mod filter;

/// creates a file traverser for javascript packages
pub fn create_js_traverser(base_path: &Path) -> FileTraverser {
    FileTraverser::new(
        base_path,
        DirectoryEntryFilterChain::new()
            .with_filter(SkipNonFileOrDirectoryFilter)
            .with_filter(SkipHiddenPathsFilter)
            .with_filter(SkipFilenameFilter::new("node_modules"))
            .with_filter(PathNotContainsSegment::new(["node_modules", "dist", "build", "bin", "doc", "docs"]))
            .with_filter(IncludeFileExtensionFilter::new(["ts", "js"]))
            .with_filter(IgnoreSpecialFileExtensions::new([
                ".d.ts",
                ".config.js",
                ".spec.js",
                ".spec.ts"
            ]))
    )
}

/// creates a file traverser for java packages
pub fn create_java_traverser(base_path: &Path) -> FileTraverser {
    FileTraverser::new(
        base_path,
        DirectoryEntryFilterChain::new()
            .with_filter(SkipNonFileOrDirectoryFilter)
            .with_filter(SkipHiddenPathsFilter)
            .with_filter(IncludeFileExtensionFilter::new(["java"]))
    )
}

/// creates a file traverser for python packages
pub fn create_python_traverser(base_path: &Path) -> FileTraverser {
    FileTraverser::new(
        base_path,
        DirectoryEntryFilterChain::new()
            .with_filter(SkipNonFileOrDirectoryFilter)
            .with_filter(SkipHiddenPathsFilter)
            .with_filter(IncludeFileExtensionFilter::new(["py"]))
    )
}

/// Traverses through files in a directory, using filters to skip directories and files. Use this
/// for extracting information from files.
pub struct FileTraverser {
    walker: WalkDir,
    filter_chain: DirectoryEntryFilterChain,
}

impl FileTraverser {
    pub fn new(base_path: &Path, directory_entry_filter_chain: DirectoryEntryFilterChain) -> Self {
        let walker = WalkDir::new(base_path);

        Self {
            walker,
            filter_chain: directory_entry_filter_chain
        }
    }
}

impl IntoIterator for FileTraverser {
    type Item = DirEntry;
    type IntoIter = FileTraverserIter;

    fn into_iter(self) -> Self::IntoIter {
        FileTraverserIter {
            walker_iter: self.walker.into_iter(),
            filter_chain: self.filter_chain,
        }
    }
}

pub struct FileTraverserIter {
    walker_iter: walkdir::IntoIter,
    filter_chain: DirectoryEntryFilterChain,
}

impl Iterator for FileTraverserIter {
    type Item = DirEntry;

    fn next(&mut self) -> Option<Self::Item> {
        loop {
            let Some(next_entry) = self.walker_iter.next() else {
                break None;
            };

            // skip erroneous entries
            let Ok(entry) = next_entry else {
                continue;
            };

            trace!("produced path: {}", entry.path().to_string_lossy());

            // check if we should skip this directory
            if entry.path().is_dir() && self.filter_chain.skip_directory(entry.path()) {
                self.walker_iter.skip_current_dir();
                continue;
            }
            
            // otherwise, check if we can take this entry
            if self.filter_chain.accept(entry.path()) {
                break Some(entry);
            }
        }
    }
}
