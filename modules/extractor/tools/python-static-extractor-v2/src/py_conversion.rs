use pyo3::{Bound, PyAny, PyResult};
use pyo3::types::{PyAnyMethods, PyInt, PyString, PyStringMethods};
use shared::regex_entity::ParsedRegexEntity;

/// Take a python RegexpInstance and convert it into a ParsedRegexEntity
pub fn convert_py_regex_entity(regex_entity_obj: Bound<PyAny>, parent_path: &str) -> PyResult<ParsedRegexEntity> {
    // let funcName = regex_entity_obj.getattr("funcName")?.downcast::<PyString>()?;
    let pattern_attr =  regex_entity_obj.getattr("pattern")?;
    let pattern = pattern_attr.downcast::<PyString>()?;
    let flags_attr = regex_entity_obj.getattr("flags")?;
    let flags = flags_attr.downcast::<PyString>()?;
    let lineno_attr = regex_entity_obj.getattr("lineno")?;
    let lineno = lineno_attr.downcast::<PyInt>()?;
    
    let entity = ParsedRegexEntity::new(
        pattern.to_string_lossy().as_ref(),
        flags.to_string_lossy().as_ref(),
        lineno.extract::<usize>()?,
        parent_path
    );
    
    Ok(entity)
}
