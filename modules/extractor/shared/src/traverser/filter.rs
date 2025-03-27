use std::collections::HashSet;
use std::ffi::OsStr;
use std::path::Path;
use log::{trace};

pub trait DirectoryEntryFilter {
    fn accept(&self, path: &Path) -> bool;
    /// Determines if we should skip this path entirely. Default judgement is false (i.e. don't skip)
    fn skip_directory(&self, _path: &Path) -> bool {
        false
    }
    fn reason(&self) -> &'static str { "unknown" }
}

pub struct DirectoryEntryFilterChain {
    filters: Vec<Box<dyn DirectoryEntryFilter>>,
}

impl DirectoryEntryFilterChain {
    pub fn new() -> Self {
        Self {
            filters: Vec::default()
        }
    }

    pub fn with_filter<FilterT: DirectoryEntryFilter + 'static>(mut self, filter: FilterT) -> Self {
        let entry: Box<dyn DirectoryEntryFilter> = Box::new(filter);
        self.filters.push(entry);
        self
    }
}

impl DirectoryEntryFilter for DirectoryEntryFilterChain {
    fn accept(&self, path: &Path) -> bool {
        for filter in &self.filters {
            if !filter.accept(path) {
                trace!("Rejecting path '{}' for reason: {}", path.to_string_lossy(), filter.reason());
                return false
            }
        }

        true
    }

    fn skip_directory(&self, path: &Path) -> bool {
        for filter in &self.filters {
            if filter.skip_directory(path) {
                trace!("Skipping directory '{}' for reason: {}", path.to_string_lossy(), filter.reason());
                return true
            }
        }

        false
    }
}

/// only keeps entries that are files or directories
pub struct SkipNonFileOrDirectoryFilter;

impl DirectoryEntryFilter for SkipNonFileOrDirectoryFilter {
    fn accept(&self, path: &Path) -> bool {
        path.is_file()
    }

    fn reason(&self) -> &'static str {
        "path must be a file"
    }
}

pub struct SkipHiddenPathsFilter;

impl SkipHiddenPathsFilter {
    fn filename_starts_with_dot(&self, path: &Path) -> bool {
        path.file_name()
            .and_then(|filename| filename.to_str())
            .is_some_and(|filename| filename.chars().take(1).any(|ch| ch == '.'))
    }
}


impl DirectoryEntryFilter for SkipHiddenPathsFilter {
    fn accept(&self, path: &Path) -> bool {
        !self.filename_starts_with_dot(path)
    }

    fn skip_directory(&self, path: &Path) -> bool {
        self.filename_starts_with_dot(path)
    }

    fn reason(&self) -> &'static str {
        "file must not be hidden (i.e. must not be prefixed with '.')"
    }
}

pub struct IncludeFileExtensionFilter {
    extensions: HashSet<String>,
}

impl IncludeFileExtensionFilter {
    pub fn new<ItemT: Into<String>, IterT: IntoIterator<Item=ItemT>>(extensions: IterT) -> Self {

        let extensions = extensions.into_iter()
            .map(Into::into)
            .collect::<HashSet<_>>();

        Self { extensions }
    }
}

impl DirectoryEntryFilter for IncludeFileExtensionFilter {
    fn accept(&self, path: &Path) -> bool {
        path.extension()
            .and_then(|extension| extension.to_str())
            .is_some_and(|extension| self.extensions.contains(extension))
    }

    fn reason(&self) -> &'static str {
        "file must have given file extension"
    }
}

pub struct SkipFilenameFilter {
    filename: String
}

impl SkipFilenameFilter {
    pub fn new<StrT: Into<String>>(name: StrT) -> Self {
        Self {
            filename: name.into()
        }
    }
}

impl DirectoryEntryFilter for SkipFilenameFilter {
    fn accept(&self, path: &Path) -> bool {
        path.file_name()
            .and_then(|filename| filename.to_str())
            .is_some_and(|filename| filename != &self.filename)
    }

    fn reason(&self) -> &'static str {
        "the given filename is skipped"
    }
}

pub struct PathNotContainsSegment {
    bad_segments: HashSet<String>
}

impl PathNotContainsSegment {
    pub fn new<ItemT: Into<String>, IterT: IntoIterator<Item=ItemT>>(segments: IterT) -> Self {

        let segments = segments.into_iter()
            .map(Into::into)
            .collect::<HashSet<_>>();

        Self { bad_segments: segments }
    }
}

pub struct IgnoreSpecialFileExtensions {
    bad_extensions: HashSet<String>
}

impl IgnoreSpecialFileExtensions {
    pub fn new<ItemT: Into<String>, IterT: IntoIterator<Item=ItemT>>(bad_extensions: IterT) -> Self {
        Self {
            bad_extensions: HashSet::from_iter(bad_extensions.into_iter().map(Into::into))
        }
    }
}

impl DirectoryEntryFilter for IgnoreSpecialFileExtensions {
    fn accept(&self, path: &Path) -> bool {
        path.file_name()
            .and_then(OsStr::to_str)
            .is_some_and(|filename| {
                for ext in &self.bad_extensions {
                    if filename.contains(ext) {
                        return false
                    }
                }
                
                true
            })
    }

    fn reason(&self) -> &'static str {
        "file cannot contain a special file extensions"
    }
}

impl DirectoryEntryFilter for PathNotContainsSegment {
    fn accept(&self, path: &Path) -> bool {
        for component in path.components().into_iter().filter_map(|component| component.as_os_str().to_str()) {
            if self.bad_segments.contains(component) {
                return false
            }
        }
        
        true
    }

    fn reason(&self) -> &'static str {
        "the path must not contain the provided path segment"
    }
}
