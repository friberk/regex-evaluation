use polars::datatypes::AnyValue;
use rusqlite::types::ValueRef;
use rust_xlsxwriter::{ColNum, RowNum, Worksheet, XlsxError};

pub fn write_polars_value<'ws, 'v>(worksheet: &'ws mut Worksheet, row: RowNum, col: ColNum, polars_value: AnyValue<'v>) -> Result<&'ws mut Worksheet, XlsxError> {
    match polars_value {
        AnyValue::Null => Ok(worksheet),
        AnyValue::Boolean(v) => worksheet.write_boolean(row, col, v),
        AnyValue::String(s) => worksheet.write_string(row, col, s),
        AnyValue::UInt8(val) => worksheet.write(row, col, val),
        AnyValue::UInt16(val) => worksheet.write(row, col, val),
        AnyValue::UInt32(val) => worksheet.write(row, col, val),
        AnyValue::UInt64(val) => worksheet.write(row, col, val),
        AnyValue::Int8(val) => worksheet.write(row, col, val),
        AnyValue::Int16(val) => worksheet.write(row, col, val),
        AnyValue::Int32(val) => worksheet.write(row, col, val),
        AnyValue::Int64(val) => worksheet.write(row, col, val),
        AnyValue::Float32(val) => worksheet.write(row, col, val),
        AnyValue::Float64(val) => worksheet.write(row, col, val),
        AnyValue::Date(val) => worksheet.write(row, col, val),
        AnyValue::StringOwned(val) => worksheet.write_string(row, col, val),
        _ => panic!("unsupported polars data type")
    }
}

pub fn convert_sqlite_value_ref<'sql, 'df>(value_ref: ValueRef<'sql>) -> AnyValue<'df> {
    match value_ref {
        ValueRef::Null => AnyValue::Null,
        ValueRef::Integer(ival) => AnyValue::from(ival),
        ValueRef::Real(rval) => AnyValue::from(rval),
        ValueRef::Text(bytes) => {
            let text_str = std::str::from_utf8(bytes).expect("All database data should be utf-8 compatible?");
            let text_str_owned = String::from(text_str);
            AnyValue::StringOwned(text_str_owned.into())
        }
        _ => panic!("unsupport sqlite datatype")
    }
}