from genson import SchemaBuilder
import json

# Load your JSON data from a file
with open('large_data.json', 'r') as f:
    data = json.load(f)

# If your JSON data is a list of objects, you can iterate over it.
# For a single large object, add it directly.
builder = SchemaBuilder()
if isinstance(data, list):
    for item in data:
        builder.add_object(item)
else:
    builder.add_object(data)

# Generate and print the schema
schema = builder.to_schema()
print(json.dumps(schema, indent=2))
