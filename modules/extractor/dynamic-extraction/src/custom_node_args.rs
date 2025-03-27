use std::collections::HashMap;
use std::fmt::{Display, Formatter};
use subprocess::Exec;

#[derive(Default, Clone)]
pub struct CustomNodeArgs {
    args: HashMap<String, String>,
}

impl CustomNodeArgs {
    pub fn new() -> Self {
        Self {
            args: HashMap::new(),
        }
    }

    pub fn parse<StrT: AsRef<str>>(raw_command_line: StrT) -> Result<Self, ()> {
        let mut custom_args = Self::new();
        let mut last_token: Option<&str> = None;
        for token in raw_command_line.as_ref().split_whitespace() {
            if token.starts_with("-") {
                match last_token {
                    None => {
                        last_token = Some(token);
                    }
                    Some(flag) => {
                        custom_args.add_flag(flag);
                        last_token = Some(token);
                    }
                }
            } else if let Some(cmd) = last_token {
                custom_args.add_arg(cmd, token);
                last_token = None;
            } else {
                panic!("Some unexpected state: last_token='{:?}' token='{}'", last_token, token);
            }
        }
        
        Ok(custom_args)
    }
    
    pub fn add_arg<StrT: Into<String>>(&mut self, arg: StrT, arg_opt: StrT) {
        self.args.insert(arg.into(), arg_opt.into());
    }

    pub fn add_flag<StrT: Into<String>>(&mut self, flag: StrT) {
        self.args.insert(flag.into(), "".to_string());
    }
    
    /// actually place these node options into a command's env
    pub fn modify_command(self, cmd: Exec) -> Exec {
        cmd.env("NODE_OPTIONS", self.to_string())
    }
}

impl From<HashMap<String, String>> for CustomNodeArgs {
    fn from(value: HashMap<String, String>) -> Self {
        Self {
            args: value
        }
    }
}

impl Display for CustomNodeArgs {
    fn fmt(&self, f: &mut Formatter<'_>) -> std::fmt::Result {
        for (key, value) in &self.args {
            write!(f, "{} {} ", key, value)?;
        }
        
        Ok(())
    }
}

#[cfg(test)]
mod test {
    use crate::custom_node_args::CustomNodeArgs;

    fn assert_has_arg(args: &CustomNodeArgs, key: &str, expected_value: &str) {
        let actual_value = args.args.get(key).expect(format!("{key} should be in map").as_str());
        assert_eq!(actual_value, expected_value);
    }
    
    fn assert_has_flag(args: &CustomNodeArgs, flag: &str) {
        let actual_value = args.args.get(flag).expect(format!("{flag} should be in map").as_str());
        assert!(actual_value.is_empty());
    }
    
    #[test]
    fn parse_works_correctly() {
        let input_str = "-r some_long_value --flag --flag-again --arg arg_value";
        let args = CustomNodeArgs::parse(input_str).expect("Should not end in error state");
        assert_has_arg(&args, "-r", "some_long_value");
        assert_has_flag(&args, "--flag");
        assert_has_flag(&args, "--flag-again");
        assert_has_arg(&args, "--arg", "arg_value");
    }
}
