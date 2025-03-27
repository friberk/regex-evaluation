package parsers.java;

import com.fasterxml.jackson.core.JsonGenerator;
import com.fasterxml.jackson.databind.SerializerProvider;
import com.fasterxml.jackson.databind.ser.std.StdSerializer;

import java.io.IOException;

public class RegexObjectSerializer extends StdSerializer<RegexObject> {

    public RegexObjectSerializer() {
        super((Class<RegexObject>) null);
    }

    public RegexObjectSerializer(Class<RegexObject> t) {
        super(t);
    }

    @Override
    public void serialize(RegexObject regexObject, JsonGenerator jsonGenerator, SerializerProvider serializerProvider) throws IOException {
        jsonGenerator.writeStartObject();
        jsonGenerator.writeStringField("pattern", regexObject.getPattern());
        jsonGenerator.writeStringField("flags", regexObject.getFlags());
        jsonGenerator.writeStringField("source_file", regexObject.getSourceFile());
        jsonGenerator.writeNumberField("line_no", regexObject.getLineNo());
        jsonGenerator.writeEndObject();
    }
}
