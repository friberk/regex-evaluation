use std::fmt::Formatter;
use std::ops::Deref;
use serde::de::{Error, Visitor};
use serde::{Deserialize, Deserializer, Serialize};

#[derive(Default, Debug, Serialize, Clone)]
pub struct SubjectString(String);

impl Into<String> for SubjectString {
    fn into(self) -> String {
        self.0
    }
}

impl Deref for SubjectString {
    type Target = String;

    fn deref(&self) -> &Self::Target {
        &self.0
    }
}

impl<T: ToString> From<T> for SubjectString {
    fn from(value: T) -> Self {
        Self(value.to_string())
    }
}

macro_rules! visit_number {
    ($name:ident, $num_type:ty) => {
         fn $name<E>(self, v: $num_type) -> Result<Self::Value, E> where E: Error {
            Ok(v.into())
         }
    };
}

impl<'de> Deserialize<'de> for SubjectString {
    fn deserialize<D>(deserializer: D) -> Result<Self, D::Error> where D: Deserializer<'de> {
        let visitor = SubjectDeserializerVisitor;
        deserializer.deserialize_any(visitor)
    }
}

struct SubjectDeserializerVisitor;

impl<'de> Visitor<'de> for SubjectDeserializerVisitor {
    type Value = SubjectString;

    fn expecting(&self, formatter: &mut Formatter) -> std::fmt::Result {
        write!(formatter, "expecting a subject")
    }

    visit_number!(visit_i8, i8);
    visit_number!(visit_i16, i16);
    visit_number!(visit_i32, i32);
    visit_number!(visit_i64, i64);
    visit_number!(visit_u8, u8);
    visit_number!(visit_u16, u16);
    visit_number!(visit_u32, u32);
    visit_number!(visit_u64, u64);

    fn visit_str<E>(self, v: &str) -> Result<Self::Value, E> where E: Error {
        Ok(v.into())
    }

    fn visit_string<E>(self, v: String) -> Result<Self::Value, E> where E: Error {
        Ok(v.into())
    }

    fn visit_none<E>(self) -> Result<Self::Value, E> where E: Error {
        Ok(Default::default())
    }
}
