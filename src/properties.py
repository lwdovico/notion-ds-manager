from typing import Any, Callable, Optional, List, Dict
        
class Property:
    """
    Base class for all property types.
    """

    schema_key: str = None
    read_only: bool = False

    # Optionally override these:
    python_type: Any = Any
    default_filter: str = "equals"
    extract_as_list: bool = False
    multiselect: bool = False

    def __init__(self, name: str, **options):
        self.name = name
        self.options = options  # for select and relations

    def build(self) -> dict:
        """
        Build the data source schema for this property.
        """
        schema = {self.schema_key: {}}

        # Add optional components (select options, relation data_source_id, etc.)
        if self.schema_key in ("select", "multi_select"):
            opts = self.options.get("options", [])
            schema[self.schema_key]["options"] = [{"name": o} for o in opts]

        if self.schema_key == "relation" and "data_source_id" in self.options:
            schema[self.schema_key]["data_source_id"] = self.options["data_source_id"]
            schema[self.schema_key]["single_property"] = {}

        return {self.name: schema}

    def validate_value(self, value):
        """
        Default: enforce python_type unless read-only. None values avoid validation.
        """
        if value is not None:
            if self.read_only:
                raise ValueError(f"{self.name} is read-only and cannot be set.")
    
            expected = self.python_type
            if expected != Any and not isinstance(value, expected):
                raise TypeError(
                    f"Property '{self.name}' expects {expected}, got {type(value)}"
                )

    def value(self, val):
        """
        Subclasses may override for special formatting.
        """
        self.validate_value(val)
        return {self.name: {self.schema_key: self._format_value(val)}}

    def _format_value(self, val):
        """
        Override. Defaulting to direct assignment.
        """
        return val

    def from_page_value(self, notion_data: dict):
        """
        Extracts a simple python value from the property.
        """
        block = notion_data.get(self.schema_key)
        if not block:
            return None

        if self.extract_as_list:
            return "".join(t["text"]["content"] for t in block)

        if self.multiselect:
            return [item["name"] for item in block]

        if self.schema_key == "select":
            return block["name"] if block else None

        return block

    def to_notion_filter(self, value):
        """
        Generic filter: property == value or property is_empty.
        """
        empty = value is None or (isinstance(value, str) and not value.strip())
        if empty:
            return {"property": self.name, self.schema_key: {"is_empty": True}}

        return {
            "property": self.name,
            self.schema_key: {self.default_filter: value}
        }

class Title(Property):
    schema_key = "title"
    python_type = str
    extract_as_list = True

    def _format_value(self, text: str):
        return [{"type": "text", "text": {"content": text}}]


class RichText(Property):
    schema_key = "rich_text"
    python_type = str
    extract_as_list = True

    def _format_value(self, text: str):
        return [{"type": "text", "text": {"content": text}}]


class Number(Property):
    schema_key = "number"
    python_type = (int, float)

class Checkbox(Property):
    schema_key = "checkbox"
    python_type = bool

class Date(Property):
    schema_key = "date"
    python_type = (str, type(None))  # ISO string or None

    def _format_value(self, start_or_dict):
        if start_or_dict is None:
            return None
        if isinstance(start_or_dict, dict):
            return start_or_dict
        return {"start": start_or_dict}


class Select(Property):
    schema_key = "select"
    python_type = str

    def __init__(self, name: str, options=None):
        super().__init__(name, options=options or [])

    def _format_value(self, val):
        return {"name" : val}


class MultiSelect(Property):
    schema_key = "multi_select"
    python_type = list
    multiselect = True

    def __init__(self, name: str, options=None):
        super().__init__(name, options=options or [])

    def _format_value(self, val):
        return [{"name" : v} for v in val]


class Relation(Property):
    schema_key = "relation"
    python_type = list
    default_filter = "contains"

    def __init__(self, name: str, data_source_id: Optional[str] = None):
        super().__init__(name, data_source_id=data_source_id)

    def _format_value(self, ids: List[str]):
        return [{"id": r} for r in ids]


class Files(Property):
    schema_key = "files"
    python_type = list

    def to_notion_filter(self, value: bool):
        if value is True:
            return {"property": self.name, "files": {"is_not_empty": True}}
        if value is False:
            return {"property": self.name, "files": {"is_empty": True}}
        raise ValueError("Files filter only accepts True/False.")

class ReadOnlyProperty(Property):
    read_only = True
    python_type = Any

    def value(self, *args, **kwargs):
        raise ValueError(f"{self.name} is read-only and cannot be set manually.")

    def validate_value(self, value):
        raise ValueError(f"{self.name} is read-only and cannot be set.")


class CreatedTime(ReadOnlyProperty):
    schema_key = "created_time"


class LastEditedTime(ReadOnlyProperty):
    schema_key = "last_edited_time"


class CreatedBy(ReadOnlyProperty):
    schema_key = "created_by"

    def from_page_value(self, notion_data: dict):
        u = notion_data.get("created_by")
        return u.get("id") if u else None


class LastEditedBy(ReadOnlyProperty):
    schema_key = "last_edited_by"

    def from_page_value(self, notion_data: dict):
        u = notion_data.get("last_edited_by")
        return u.get("id") if u else None

class Properties:
    """Aggregate data source schema definitions."""
    def __init__(self, *props: Property):
        self.props = props

    def build(self) -> dict:
        return {k: v for p in self.props for k, v in p.build().items()}


class PageProperties:
    """Aggregate page property values."""
    def __init__(self, *values: dict):
        self.values = values

    def build(self) -> dict:
        return {k: v for obj in self.values for k, v in obj.items()}


class PropertyTypes:
    
    PROPERTY_TYPES = {
                      "title": Title,
                      "rich_text": RichText,
                      "number": Number,
                      "checkbox": Checkbox,
                      "date": Date,
                      "created_time": CreatedTime,
                      "last_edited_time": LastEditedTime,
                      "created_by": CreatedBy,
                      "last_edited_by": LastEditedBy,
                      "select": Select,
                      "multi_select": MultiSelect,
                      "relation": Relation,
                      "files": Files
                     }
    
    @classmethod
    def get_property_class(cls, property_type):
        """
        A method to retrieve the class from PROPERTY_TYPES.
        """
        class_or_name = cls.PROPERTY_TYPES.get(property_type)
        
        if isinstance(class_or_name, str):
            if class_or_name == cls.__name__:
                return cls

        return class_or_name

class Rollup(ReadOnlyProperty):
    """
    Rollup fields are read-only and cannot be set manually.
    It delegates value parsing to PropertyTypes where possible.
    """

    schema_key = "rollup"

    def __init__(self, name: str, relation_property_name: str, rollup_property_name: str, function: str):
        super().__init__(name)
        self.relation_property_name = relation_property_name
        self.rollup_property_name = rollup_property_name
        self.function = function

    def build(self):
        return {
            self.name: {
                "rollup": {
                    "relation_property_name": self.relation_property_name,
                    "rollup_property_name": self.rollup_property_name,
                    "function": self.function,
                }
            }
        }

    def from_page_value(self, notion_data: dict):
        """
        Rollups return dynamic data. We try to
        delegate parsing based on the rollup type.
        """
        rollup_data = notion_data.get("rollup")
        if not rollup_data:
            return None

        rollup_type = rollup_data.get("type")

        if rollup_type == "array":
            array_content = rollup_data.get("array", [])
            if not array_content:
                return []

            first_item = array_content[0]
            content_type = first_item.get("type")

            PropClass = PropertyTypes.get_property_class(content_type)
            if PropClass:
                parser = PropClass("__rollup__tmp__")
                return [parser.from_page_value(item) for item in array_content]

            return array_content

        PropClass = PropertyTypes.get_property_class(rollup_type)

        if PropClass:
            parser = PropClass("__rollup__tmp__")
            return parser.from_page_value(rollup_data)

        return rollup_data

    def to_notion_filter(self, value):
        raise NotImplementedError(
            f"Rollup filters are not yet implemented for '{self.name}'."
        )

PropertyTypes.PROPERTY_TYPES.update({ "rollup" : Rollup })