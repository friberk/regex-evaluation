mod subject;

use std::path::{Path, PathBuf};
use serde::{Deserialize, Serialize};
use crate::package_spec::PackageSpec;
use crate::usage::subject::SubjectString;

/// describes a "regex usage," i.e., a regex pattern and a subject string that was evaluated on the
/// regex. This is an intermediate data structure that represents a raw logged entry. This should
/// not be used directly.
#[derive(Deserialize, Serialize, Debug, Clone)]
pub struct RawUsageRecord {
    pattern: String,
    subject: SubjectString,
    stack: String,
    #[serde(rename = "funcName")]
    func_name: String,
}

impl RawUsageRecord {
    pub fn pattern(&self) -> &str {
        &self.pattern
    }
}

/// Represents a fully formed regex usage entity.
#[derive(Deserialize, Serialize, Debug, Clone)]
pub struct UsageRecord {
    pattern: String,
    subject: String,
    stack: String,
    #[serde(rename = "funcName")]
    func_name: String,
    project_repo_url: String,
    project_base_path: PathBuf,
}

impl UsageRecord {

    pub fn from_parsed<PathBufT: Into<PathBuf>>(raw_usage_record: RawUsageRecord, package_spec: &PackageSpec, base_path: PathBufT) -> Self {
        Self {
            pattern: raw_usage_record.pattern,
            subject: raw_usage_record.subject.into(),
            stack: raw_usage_record.stack,
            func_name: raw_usage_record.func_name,
            project_repo_url: package_spec.repo().to_string(),
            project_base_path: base_path.into(),
        }
    }

    pub fn pattern(&self) -> &str {
        &self.pattern
    }
    pub fn subject(&self) -> &str {
        &self.subject
    }
    pub fn stack(&self) -> &str {
        &self.stack
    }
    pub fn func_name(&self) -> &str {
        &self.func_name
    }
    pub fn project_url(&self) -> &str {
        &self.project_repo_url
    }
    pub fn project_base_path(&self) -> &Path {
        &self.project_base_path
    }
}

#[cfg(test)]
mod tests {
    use crate::usage::RawUsageRecord;

    #[test]
    fn pars_record_normal() {
        let raw = r#"{"pattern":"^function .*?\\(\\) \\{ \\[native code\\] \\}$", "subject": "hello world", "stack":"Error\n    at RegExp.test (/tmp/sourcetrace/test.js:32:19)\n    at isNative (/tmp/sourcetrace/node_modules/lodash/dist/lodash.js:1484:53)\n    at runInContext (/tmp/sourcetrace/node_modules/lodash/dist/lodash.js:480:26)\n    at Object.<anonymous> (/tmp/sourcetrace/node_modules/lodash/dist/lodash.js:6756:11)\n    at Object.<anonymous> (/tmp/sourcetrace/node_modules/lodash/dist/lodash.js:6786:3)\n    at Module._compile (node:internal/modules/cjs/loader:1376:14)\n    at Module._extensions..js (node:internal/modules/cjs/loader:1435:10)\n    at Module.load (node:internal/modules/cjs/loader:1207:32)\n    at Module._load (node:internal/modules/cjs/loader:1023:12)\n    at Module.require (node:internal/modules/cjs/loader:1235:19)\n    at require (node:internal/modules/helpers:176:18)\n    at Object.<anonymous> (/tmp/sourcetrace/sourcetrace.js:128:9)\n    at Module._compile (node:internal/modules/cjs/loader:1376:14)\n    at Module._extensions..js (node:internal/modules/cjs/loader:1435:10)\n    at Module.load (node:internal/modules/cjs/loader:1207:32)\n    at Module._load (node:internal/modules/cjs/loader:1023:12)\n    at Module.require (node:internal/modules/cjs/loader:1235:19)\n    at require (node:internal/modules/helpers:176:18)\n    at Object.<anonymous> (/tmp/sourcetrace/test.js:131:19)\n    at Module._compile (node:internal/modules/cjs/loader:1376:14)\n    at Module._extensions..js (node:internal/modules/cjs/loader:1435:10)\n    at Module.load (node:internal/modules/cjs/loader:1207:32)\n    at Module._load (node:internal/modules/cjs/loader:1023:12)\n    at Module.require (node:internal/modules/cjs/loader:1235:19)\n    at require (node:internal/modules/helpers:176:18)\n    at /tmp/sourcetrace/node_modules/mocha/lib/mocha.js:172:27\n    at Array.forEach (<anonymous>)\n    at Mocha.loadFiles (/tmp/sourcetrace/node_modules/mocha/lib/mocha.js:169:14)\n    at Mocha.run (/tmp/sourcetrace/node_modules/mocha/lib/mocha.js:356:31)\n    at Object.<anonymous> (/tmp/sourcetrace/node_modules/mocha/bin/_mocha:366:16)\n    at Module._compile (node:internal/modules/cjs/loader:1376:14)\n    at Module._extensions..js (node:internal/modules/cjs/loader:1435:10)\n    at Module.load (node:internal/modules/cjs/loader:1207:32)\n    at Module._load (node:internal/modules/cjs/loader:1023:12)\n    at Function.executeUserEntryPoint [as runMain] (node:internal/modules/run_main:135:12)\n    at node:internal/main/run_main_module:28:49","funcName":"test","def":false}"#;
        let record = serde_json::from_str::<RawUsageRecord>(raw).expect("should parse successfully");
        assert_eq!(record.subject.as_str(), "hello world")
    }

    #[test]
    fn parse_record_no_subject() {
        let raw = r#"{"pattern":"^function .*?\\(\\) \\{ \\[native code\\] \\}$","stack":"Error\n    at RegExp.test (/tmp/sourcetrace/test.js:32:19)\n    at isNative (/tmp/sourcetrace/node_modules/lodash/dist/lodash.js:1484:53)\n    at runInContext (/tmp/sourcetrace/node_modules/lodash/dist/lodash.js:480:26)\n    at Object.<anonymous> (/tmp/sourcetrace/node_modules/lodash/dist/lodash.js:6756:11)\n    at Object.<anonymous> (/tmp/sourcetrace/node_modules/lodash/dist/lodash.js:6786:3)\n    at Module._compile (node:internal/modules/cjs/loader:1376:14)\n    at Module._extensions..js (node:internal/modules/cjs/loader:1435:10)\n    at Module.load (node:internal/modules/cjs/loader:1207:32)\n    at Module._load (node:internal/modules/cjs/loader:1023:12)\n    at Module.require (node:internal/modules/cjs/loader:1235:19)\n    at require (node:internal/modules/helpers:176:18)\n    at Object.<anonymous> (/tmp/sourcetrace/sourcetrace.js:128:9)\n    at Module._compile (node:internal/modules/cjs/loader:1376:14)\n    at Module._extensions..js (node:internal/modules/cjs/loader:1435:10)\n    at Module.load (node:internal/modules/cjs/loader:1207:32)\n    at Module._load (node:internal/modules/cjs/loader:1023:12)\n    at Module.require (node:internal/modules/cjs/loader:1235:19)\n    at require (node:internal/modules/helpers:176:18)\n    at Object.<anonymous> (/tmp/sourcetrace/test.js:131:19)\n    at Module._compile (node:internal/modules/cjs/loader:1376:14)\n    at Module._extensions..js (node:internal/modules/cjs/loader:1435:10)\n    at Module.load (node:internal/modules/cjs/loader:1207:32)\n    at Module._load (node:internal/modules/cjs/loader:1023:12)\n    at Module.require (node:internal/modules/cjs/loader:1235:19)\n    at require (node:internal/modules/helpers:176:18)\n    at /tmp/sourcetrace/node_modules/mocha/lib/mocha.js:172:27\n    at Array.forEach (<anonymous>)\n    at Mocha.loadFiles (/tmp/sourcetrace/node_modules/mocha/lib/mocha.js:169:14)\n    at Mocha.run (/tmp/sourcetrace/node_modules/mocha/lib/mocha.js:356:31)\n    at Object.<anonymous> (/tmp/sourcetrace/node_modules/mocha/bin/_mocha:366:16)\n    at Module._compile (node:internal/modules/cjs/loader:1376:14)\n    at Module._extensions..js (node:internal/modules/cjs/loader:1435:10)\n    at Module.load (node:internal/modules/cjs/loader:1207:32)\n    at Module._load (node:internal/modules/cjs/loader:1023:12)\n    at Function.executeUserEntryPoint [as runMain] (node:internal/modules/run_main:135:12)\n    at node:internal/main/run_main_module:28:49","funcName":"test","def":false}"#;
        let _record = serde_json::from_str::<RawUsageRecord>(raw).expect("should parse successfully");
    }

    #[test]
    fn parse_record_null_subject() {
        let raw = r#"{"pattern":"^function .*?\\(\\) \\{ \\[native code\\] \\}$", "subject": null, "funcName":"test","def":false, "stack":"Error\n    at RegExp.test (/tmp/sourcetrace/test.js:32:19)\n    at isNative (/tmp/sourcetrace/node_modules/lodash/dist/lodash.js:1484:53)\n    at runInContext (/tmp/sourcetrace/node_modules/lodash/dist/lodash.js:480:26)\n    at Object.<anonymous> (/tmp/sourcetrace/node_modules/lodash/dist/lodash.js:6756:11)\n    at Object.<anonymous> (/tmp/sourcetrace/node_modules/lodash/dist/lodash.js:6786:3)\n    at Module._compile (node:internal/modules/cjs/loader:1376:14)\n    at Module._extensions..js (node:internal/modules/cjs/loader:1435:10)\n    at Module.load (node:internal/modules/cjs/loader:1207:32)\n    at Module._load (node:internal/modules/cjs/loader:1023:12)\n    at Module.require (node:internal/modules/cjs/loader:1235:19)\n    at require (node:internal/modules/helpers:176:18)\n    at Object.<anonymous> (/tmp/sourcetrace/sourcetrace.js:128:9)\n    at Module._compile (node:internal/modules/cjs/loader:1376:14)\n    at Module._extensions..js (node:internal/modules/cjs/loader:1435:10)\n    at Module.load (node:internal/modules/cjs/loader:1207:32)\n    at Module._load (node:internal/modules/cjs/loader:1023:12)\n    at Module.require (node:internal/modules/cjs/loader:1235:19)\n    at require (node:internal/modules/helpers:176:18)\n    at Object.<anonymous> (/tmp/sourcetrace/test.js:131:19)\n    at Module._compile (node:internal/modules/cjs/loader:1376:14)\n    at Module._extensions..js (node:internal/modules/cjs/loader:1435:10)\n    at Module.load (node:internal/modules/cjs/loader:1207:32)\n    at Module._load (node:internal/modules/cjs/loader:1023:12)\n    at Module.require (node:internal/modules/cjs/loader:1235:19)\n    at require (node:internal/modules/helpers:176:18)\n    at /tmp/sourcetrace/node_modules/mocha/lib/mocha.js:172:27\n    at Array.forEach (<anonymous>)\n    at Mocha.loadFiles (/tmp/sourcetrace/node_modules/mocha/lib/mocha.js:169:14)\n    at Mocha.run (/tmp/sourcetrace/node_modules/mocha/lib/mocha.js:356:31)\n    at Object.<anonymous> (/tmp/sourcetrace/node_modules/mocha/bin/_mocha:366:16)\n    at Module._compile (node:internal/modules/cjs/loader:1376:14)\n    at Module._extensions..js (node:internal/modules/cjs/loader:1435:10)\n    at Module.load (node:internal/modules/cjs/loader:1207:32)\n    at Module._load (node:internal/modules/cjs/loader:1023:12)\n    at Function.executeUserEntryPoint [as runMain] (node:internal/modules/run_main:135:12)\n    at node:internal/main/run_main_module:28:49"}"#;
        let record = serde_json::from_str::<RawUsageRecord>(raw).expect("should parse successfully");
        assert_eq!(record.subject.as_str(), "")
    }

    #[test]
    fn parse_record_number_subject() {
        let raw = r#"{"pattern":"^function .*?\\(\\) \\{ \\[native code\\] \\}$", "subject": 2433, "funcName":"test","def":false, "stack":"Error\n    at RegExp.test (/tmp/sourcetrace/test.js:32:19)\n    at isNative (/tmp/sourcetrace/node_modules/lodash/dist/lodash.js:1484:53)\n    at runInContext (/tmp/sourcetrace/node_modules/lodash/dist/lodash.js:480:26)\n    at Object.<anonymous> (/tmp/sourcetrace/node_modules/lodash/dist/lodash.js:6756:11)\n    at Object.<anonymous> (/tmp/sourcetrace/node_modules/lodash/dist/lodash.js:6786:3)\n    at Module._compile (node:internal/modules/cjs/loader:1376:14)\n    at Module._extensions..js (node:internal/modules/cjs/loader:1435:10)\n    at Module.load (node:internal/modules/cjs/loader:1207:32)\n    at Module._load (node:internal/modules/cjs/loader:1023:12)\n    at Module.require (node:internal/modules/cjs/loader:1235:19)\n    at require (node:internal/modules/helpers:176:18)\n    at Object.<anonymous> (/tmp/sourcetrace/sourcetrace.js:128:9)\n    at Module._compile (node:internal/modules/cjs/loader:1376:14)\n    at Module._extensions..js (node:internal/modules/cjs/loader:1435:10)\n    at Module.load (node:internal/modules/cjs/loader:1207:32)\n    at Module._load (node:internal/modules/cjs/loader:1023:12)\n    at Module.require (node:internal/modules/cjs/loader:1235:19)\n    at require (node:internal/modules/helpers:176:18)\n    at Object.<anonymous> (/tmp/sourcetrace/test.js:131:19)\n    at Module._compile (node:internal/modules/cjs/loader:1376:14)\n    at Module._extensions..js (node:internal/modules/cjs/loader:1435:10)\n    at Module.load (node:internal/modules/cjs/loader:1207:32)\n    at Module._load (node:internal/modules/cjs/loader:1023:12)\n    at Module.require (node:internal/modules/cjs/loader:1235:19)\n    at require (node:internal/modules/helpers:176:18)\n    at /tmp/sourcetrace/node_modules/mocha/lib/mocha.js:172:27\n    at Array.forEach (<anonymous>)\n    at Mocha.loadFiles (/tmp/sourcetrace/node_modules/mocha/lib/mocha.js:169:14)\n    at Mocha.run (/tmp/sourcetrace/node_modules/mocha/lib/mocha.js:356:31)\n    at Object.<anonymous> (/tmp/sourcetrace/node_modules/mocha/bin/_mocha:366:16)\n    at Module._compile (node:internal/modules/cjs/loader:1376:14)\n    at Module._extensions..js (node:internal/modules/cjs/loader:1435:10)\n    at Module.load (node:internal/modules/cjs/loader:1207:32)\n    at Module._load (node:internal/modules/cjs/loader:1023:12)\n    at Function.executeUserEntryPoint [as runMain] (node:internal/modules/run_main:135:12)\n    at node:internal/main/run_main_module:28:49"}"#;
        let record = serde_json::from_str::<RawUsageRecord>(raw).expect("should parse successfully");
        assert_eq!(record.subject.as_str(), "2433")
    }

    #[test]
    fn parse_production_1() {
        let raw = r#"{"pattern": "\\s+", "subject": "cpuset   0       129     1", "funcName": "Matcher#find", "stack": ""}"#;
        let record = serde_json::from_str::<RawUsageRecord>(raw).expect("Should successfully parse");
        assert_eq!(record.func_name, "Matcher#find");
    }

    #[test]
    fn parse_production_2() {
        let raw = r#"{"pattern": "(>>)|(>)|(\")|(')", "subject": "GET /path/work1 --param1 apple --param2=straw\\berry --arr=a --arr=\\b >> a\\bcde.txt > 12345.txt", "funcName": "Matcher#find", "stack": ""}"#;
        let record = serde_json::from_str::<RawUsageRecord>(raw).expect("Should successfully parse");
        assert_eq!(record.func_name, "Matcher#find");
    }

    #[test]
    fn parse_production_3() {
        let raw = r#"{"pattern": "^(?:%(?<MOD>!?[0-9,]+)?(?:\\{(?<ARG>[^}]+)})?(?<CODE>(?:(?:ti)|(?:to)|[a-zA-Z%]))|(?<LITERAL>[^%]+))(?<REMAINING>.*)", "subject": " \"%\\{Referer\\}i\" \"%\\{User-Agent\\}i\"", "funcName": "Matcher#matches", "stack": ""}"#;
        let record = serde_json::from_str::<RawUsageRecord>(raw).expect("Should successfully parse");
        assert_eq!(record.func_name, "Matcher#matches");
    }

    #[test]
    fn parse_production_4() {
        let raw = r#"{"pattern": "^[^\\s]\\s+\\^\\]+\\\+[\\\s]+\\s+(\\^\s]\\)\s\\([^\s]+\\\s+[\\-]+\\\s+([^\s]+)\s+.*$", "subject": "394 26 8:18 / /run/media/anonymous/Windows\\040Extr\\\040Storage rw,nosuid,nodev,relatime shared:569 - ntfs3 /dev/\bdb2 rw,uid=1000,gid=1000,iocharset=utf8", "funcName": "Matcher#matches", "stack": ""}"#;
        let record = serde_json::from_str::<RawUsageRecord>(raw).expect("Should successfully parse");
        assert_eq!(record.func_name, "Matcher#matches");
    }
}
