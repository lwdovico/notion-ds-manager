class Property:
    """
    Base class for all property types.
    """
    def __init__(self, name: str):
        self.name = name

    def build(self):
        raise NotImplementedError

    def value(self, *args, **kwargs):
        """
        For building page property values.
        Children override this.
        """
        raise NotImplementedError
            
    def validate_value(self, value):
        """
        Validate the input value type.
        Children override this.
        """
        pass

    def to_page_value(self, value, name):
        """
        Build the final page value dict. 
        Implements value() logic.
        """
        return self.value(value)
            
    def from_page_value(self, notion_data: dict):
        """Extracts the simple Python value from the Notion API response."""
        return None
    
    def to_notion_filter(self, value):
        """Generates the Notion API filter object. Subclasses MUST override this."""
        raise NotImplementedError(f"Filtering not implemented for {self.__class__.__name__}")

class Title(Property):
    def build(self):
        return {self.name: {"title": {}}}

    def value(self, text: str):
        return {
            self.name: {
                "title": [{"type": "text", "text": {"content": text}}]
            }
        }
        
    def validate_value(self, value):
        if not isinstance(value, str):
            raise TypeError(f"Property '{self.name}' expects a string")

    def from_page_value(self, notion_data: dict):
        if "title" in notion_data:
            return "".join([t["text"]["content"] for t in notion_data["title"]])
        return None

    def to_notion_filter(self, value):
        if value is None or str(value).strip() == '':
            return {
                "property": self.name,
                "title": {"is_empty": True}
            }
        return {
            "property": self.name,
            "title": {"contains": str(value)}
        }
        
class RichText(Property):
    def build(self):
        return {self.name: {"rich_text": {}}}

    def value(self, text: str):
        return {
            self.name: {
                "rich_text": [{"type": "text", "text": {"content": text}}]
            }
        }
        
    def validate_value(self, value):
        if not isinstance(value, str):
            raise TypeError(f"Property '{self.name}' expects a string")

    def from_page_value(self, notion_data: dict):
        if "rich_text" in notion_data:
            return "".join([t["text"]["content"] for t in notion_data["rich_text"]])
        return None
    
    def to_notion_filter(self, value):
        if value is None or str(value).strip() == '':
            return {
                "property": self.name,
                "rich_text": {"is_empty": True}
            }
        return {
            "property": self.name,
            "rich_text": {"contains": str(value)}
        }
        
class Number(Property):
    def build(self):
        return {self.name: {"number": {}}}

    def value(self, num: float):
        return {self.name: {"number": num}}

    def validate_value(self, value):
        if not isinstance(value, (int, float)):
            raise TypeError(f"Number property '{self.name}' expects an int or float")

    def from_page_value(self, notion_data: dict):
        if "number" in notion_data:
            return notion_data["number"]
        return None
            
    def to_notion_filter(self, value):
        if value is None or str(value).strip() == '':
            return {
                "property": self.name,
                "number": {"is_empty": True}
            }
        return {
            "property": self.name,
            "number": {"equals": value} # Default to 'equals'
        }
    
class Checkbox(Property):
    def build(self):
        return {self.name: {"checkbox": {}}}

    def value(self, checked: bool):
        return {self.name: {"checkbox": checked}}

    def validate_value(self, value):
        if not isinstance(value, bool):
            raise TypeError(f"Checkbox property '{self.name}' expects a boolean")
    
    def from_page_value(self, notion_data: dict):
        if "checkbox" in notion_data:
            return notion_data["checkbox"]
        return None
    
    def to_notion_filter(self, value: bool):
        return {
            "property": self.name,
            "checkbox": {"equals": value}
        }

class Date(Property):
    def build(self):
        return {self.name: {"date": {}}}

    def value(self, start: str, end: str = None):
        date_dict = None
        if start is not None:
            date_dict = {"start" : start}
            if end is not None:
                date_dict["end"] = end
                
        return {
            self.name: {
                "date": date_dict
            }
        }
        
    def validate_value(self, value):
        if not isinstance(value, str):
            raise TypeError(f"Date property '{self.name}' expects a string (ISO format)")

    def from_page_value(self, notion_data: dict):
        if "date" in notion_data:
            if notion_data["date"]:
                return notion_data["date"]["start"]
        return None
    
    def to_notion_filter(self, value: str):
        if value is None or str(value).strip() == '':
            return {
                "property": self.name,
                "date": {"is_empty": True}
            }
        return {
            "property": self.name,
            "date": {"equals": value}
            }

class CreatedTime(Property):
    def build(self):
        return {self.name: {"created_time": {}}}
        
    def value(self, *args, **kwargs):
        raise ValueError("Cannot set created_time manually")
    
    def validate_value(self, value):
        raise ValueError(f"Cannot set {self.name} property manually.")
    
    def from_page_value(self, notion_data: dict):
        """Extracts the start date/time string from the 'created_time' object."""
        return notion_data.get("created_time")
    
    def to_notion_filter(self, value: str):
        return { 
            "property": self.name, 
            "created_time": {"on_or_after": value} 
        }
        
class LastEditedTime(Property):
    def build(self):
        return {self.name: {"last_edited_time": {}}}
        
    def value(self, *args, **kwargs):
        raise ValueError("Cannot set last_edited_time manually")
        
    def validate_value(self, value):
        raise ValueError(f"Cannot set {self.name} property manually.")

    def from_page_value(self, notion_data: dict):
        """Extracts the start date/time string from the 'last_edited_time' object."""
        return notion_data.get("last_edited_time")

    def to_notion_filter(self, value: str):
        return { 
            "property": self.name, 
            "last_edited_time": {"on_or_after": value} 
        }

class CreatedBy(Property):
    def build(self):
        return {self.name: {"created_by": {}}}
        
    def value(self, *args, **kwargs):
        raise ValueError("Cannot set created_by manually")
        
    def validate_value(self, value):
        raise ValueError(f"Cannot set {self.name} property manually.")
    
    def from_page_value(self, notion_data: dict):
        """Extracts the user ID from the 'created_by' object."""
        # You could return the whole user object or just the ID/Name. ID is often most useful.
        user_info = notion_data.get("created_by")
        return user_info.get("id") if user_info else None
    
    def to_notion_filter(self, value: str):
        return { 
            "property": self.name, 
            "created_by": {"equals": value} 
        }

class LastEditedBy(Property):
    def build(self):
        return {self.name: {"last_edited_by": {}}}
        
    def value(self, *args, **kwargs):
        raise ValueError("Cannot set last_edited_by manually")
        
    def validate_value(self, value):
        raise ValueError(f"Cannot set {self.name} property manually.")
    
    def from_page_value(self, notion_data: dict):
        """Extracts the user ID from the 'last_edited_by' object."""
        user_info = notion_data.get("last_edited_by")
        return user_info.get("id") if user_info else None
    
    def to_notion_filter(self, value: str):
        # Assumes value is a user ID string for 'equals'
        return { 
            "property": self.name, 
            "last_edited_by": {"equals": value} 
        }

class Select(Property):
    def __init__(self, name: str, options=None):
        super().__init__(name)
        self.options = options or []

    def build(self):
        return {
            self.name: {
                "select": {
                    "options": [{"name": opt} for opt in self.options]
                }
            }
        }

    def value(self, name: str):
        return {self.name: {"select": {"name": name}}}

    def validate_value(self, value):
        if not isinstance(value, str):
            raise TypeError(f"Select property '{self.name}' expects a string")

    def from_page_value(self, notion_data: dict):
        if "select" in notion_data:
            if notion_data["select"]:
                return notion_data["select"]["name"]
        return None

    def to_notion_filter(self, value: str):
        if value is None or str(value).strip() == '':
            return {
                "property": self.name,
                "select": {"is_empty": True}
            }
        return {
            "property": self.name,
            "select": {"equals": value}
        }


class MultiSelect(Property):
    def __init__(self, name: str, options=None):
        super().__init__(name)
        self.options = options or []

    def build(self):
        return {
            self.name: {
                "multi_select": {
                    "options": [{"name": opt} for opt in self.options]
                }
            }
        }

    def value(self, names: list[str]):
        return {self.name: {"multi_select": [{"name": n} for n in names]}}

    def validate_value(self, value):
        if not isinstance(value, list):
            raise TypeError(f"MultiSelect property '{self.name}' expects a list of names")

    def from_page_value(self, notion_data: dict):
        if "multi_select" in notion_data:
            return [item["name"] for item in notion_data["multi_select"]]
        return None

    def to_notion_filter(self, value: str):
        if value is None or str(value).strip() == '':
            return {
                "property": self.name,
                "multi_select": {"is_empty": True}
            }
        return {
            "property": self.name,
            "multi_select": {"contains": value}
        }

class Relation(Property):
    def __init__(self, name: str, data_source_id: str = None):
        super().__init__(name)
        self.data_source_id = data_source_id

    def build(self):
        return {
            self.name: {
                "relation": {
                    "data_source_id" : self.data_source_id,
                    "single_property": {}
                }
            }
        }

    def value(self, ids: list[str]):
        return {
            self.name: {
                "relation": [{"id": r} for r in ids]
            }
        }
        
    def validate_value(self, value):
        if not isinstance(value, list):
            raise TypeError(f"Relation property '{self.name}' expects a list of IDs")


    def from_page_value(self, notion_data: dict):
        if "relation" in notion_data:
            return [r["id"] for r in notion_data["relation"]]
        return None

    def to_notion_filter(self, value: str):
        if value is None or str(value).strip() == '':
            return {
                "property": self.name,
                "relation": {"is_empty": True}
            }
        return {
            "property": self.name,
            "relation": {"contains": value}
        }

class Files(Property):
    def build(self):
        return {self.name: {"files": {}}}

    def value(self, files: list[dict]):
        """
        files: list of dicts with {"name": ..., "external": {"url": ...}} or {"file": {"url": ...}}
        """
        return {self.name: {"files": files}}

    def validate_value(self, value):
        if not isinstance(value, list):
            raise TypeError(f"Files property '{self.name}' expects a list of file dictionaries.")

    def from_page_value(self, notion_data: dict):
        # For simplicity, just return the list of file objects
        if "files" in notion_data:
            return notion_data["files"]
        return []

    def to_notion_filter(self, value: bool):
        if value is True:
            return {"property": self.name, "files": {"is_not_empty": True}}
        elif value is False:
            return {"property": self.name, "files": {"is_empty": True}}
        raise ValueError("Files filter only supports True/False (is_not_empty/is_empty).")

class Properties:
    """
    Aggregate multiple Property() definitions into a single dict.
    """

    def __init__(self, *props: Property):
        self.props = props

    def build(self):
        final = {}
        for p in self.props:
            final.update(p.build())
        return final

class PageProperties:
    """
    Build page property values.
    """
    def __init__(self, *props):
        self.props = props

    def build(self):
        final = {}
        for p in self.props:
            final.update(p)
        return final

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

class Rollup(Property):
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
            
    def value(self, *args, **kwargs):
        raise ValueError("Cannot set rollup property manually")
    
    def validate_value(self, value):
        raise ValueError(f"Cannot set {self.name} property manually.")
    
    def from_page_value(self, notion_data: dict):
        """
        Extracts the simple Python value from the Rollup object by delegating 
        to the appropriate Property class for parsing the nested types.
        """
        rollup_data = notion_data.get("rollup")
        if not rollup_data:
            return None

        rollup_type = rollup_data.get("type")
        
        if rollup_type == 'array':
            array_content = rollup_data.get('array', [])
            
            if not array_content:
                return []
            
            content_type = array_content[0].get('type')
            PropClass = PROPERTY_TYPES.get(content_type)
            
            if PropClass:
                temp_prop = PropClass(name="__temp_rollup_parser__")
                
                return [temp_prop.from_page_value(item) for item in array_content]
            
            return array_content 
        
        PropClass = PROPERTY_TYPES.get(rollup_type)
        
        if PropClass:
            temp_prop = PropClass(name="__temp_rollup_parser__")
            return temp_prop.from_page_value(rollup_data)

        return rollup_data
    
    def to_notion_filter(self, value):
        raise NotImplementedError(f"Filtering for Rollup properties is complex and not yet implemented for {self.name}")

PROPERTY_TYPES["rollup"] = Rollup

class Filter:
    """
    A class to construct complex Notion API filter objects, defaulting to 
    compound AND/OR logic for simple dictionary inputs.
    """
    def __init__(self, schema_template):
        self._schema = schema_template

    def _get_prop_filter(self, prop_name: str, value: any) -> dict:
        """Helper to get the Notion filter dict for a single property."""
        prop = self._schema.properties.get(prop_name)
        if not prop:
            raise KeyError(f"Property '{prop_name}' not found in schema for filtering.")
        return prop.to_notion_filter(value)
    
    def _create_and_block(self, simple_filter: dict) -> dict:
        """
        Internal method to convert a simple multi-key dictionary into 
        a full Notion 'and' filter block.
        """
        if not isinstance(simple_filter, dict) or not simple_filter:
            return {}

        full_filters = [
                        self._get_prop_filter(prop_name, value) 
                        for prop_name, value in simple_filter.items()
                        ]
            
        if len(full_filters) == 1:
            return full_filters[0]
            
        return {"and": full_filters}
    

    def AND(self, filters: dict | list[dict]) -> dict:
        """
        Applies a logical AND.
        Input: A single multi-key dict (treated as one AND block) 
               OR a list of multi-key dicts (treated as (x) AND (y)).
        """
        if isinstance(filters, dict):
            # Single multi-key dict, treat as one AND block (A AND B)
            return self._create_and_block(filters)
            
        if isinstance(filters, list):
            # List of multi-key dicts, create an AND block for each, 
            and_blocks = [self._create_and_block(f) for f in filters]
            
            # Remove empty blocks
            and_blocks = [f for f in and_blocks if f]

            if len(and_blocks) == 1:
                return and_blocks[0]
            
            if not and_blocks:
                return {}
                
            return {"and": and_blocks}

        raise TypeError("Input to AND must be a single dictionary or a list of dictionaries.")

    def OR(self, filters: dict | list[dict]) -> dict:
        """
        Applies a logical OR.
        Input: A single multi-key dict (treated as one AND block) 
               OR a list of multi-key dicts (treated as (x) OR (yf)).
        """
        if isinstance(filters, dict):
            # Single multi-key dict, treat as one AND block (A AND B)
            return self._create_and_block(filters)
            
        if isinstance(filters, list):
            # List of multi-key dicts, create an AND block for each, 
            and_blocks = [self._create_and_block(f) for f in filters]
            
            # Remove empty blocks
            and_blocks = [f for f in and_blocks if f]

            if len(and_blocks) == 1:
                return and_blocks[0]
            
            if not and_blocks:
                return {}
                
            return {"or": and_blocks}

        raise TypeError("Input to OR must be a single dictionary or a list of dictionaries.")

class SchemaTemplate:
    
    def __init__(self, properties: dict):
        
        self.properties = { name: prop
                            for name, prop in ((n, self.property_from_schema(n, info)) for n, info in properties.items())
                            if prop is not None }
        
        self.F = Filter(self)

    def property_from_schema(self, name: str, data: dict):
        """
        Constructor method
        """
        t = data["type"]

        PropClass = PROPERTY_TYPES.get(t)
        if PropClass is None:
            raise ValueError(f"Unknown property type {t}")

        if issubclass(PropClass, (Select, MultiSelect)):
            options = [o["name"] for o in data[t]["options"]]
            return PropClass(name, options)

        if issubclass(PropClass, Relation):
            rel_info = data.get("relation")
            if isinstance(rel_info, dict):
                data_source = rel_info.get("data_source_id")
            elif isinstance(rel_info, str):
                data_source = rel_info
            else:
                data_source = None
            return PropClass(name, data_source)

        if issubclass(PropClass, Rollup):
            rollup_info = data.get("rollup", {})
            relation_prop_name = rollup_info.get("relation_property_name")
            rollup_prop_name = rollup_info.get("rollup_property_name")
            function = rollup_info.get("function")
            # If the schema is missing critical info, return None or raise an error
            if not relation_prop_name or not rollup_prop_name or not function:
                 return None 
            return PropClass(name, relation_prop_name, rollup_prop_name, function)

        return PropClass(name)

    def to_page(self, data: dict):
        """
        Convert user values into proper notion page property dict,
        with validation for required keys, unknown keys, and value types.
        """
        props = {}
    
        unknown_keys = set(data.keys()) - set(self.properties.keys())
        if unknown_keys:
            raise KeyError(f"Unknown properties passed: {unknown_keys}")

        props = {}
        for name, value in data.items():
            prop = self.properties[name]
            
            if value is None and isinstance(prop, (CreatedTime, LastEditedTime, CreatedBy, LastEditedBy)):
                 raise ValueError(f"Cannot clear/set read-only property {name} to None.")
            
            if value is not None:
                prop.validate_value(value)

            props.update(prop.to_page_value(value, name))
    
        return props
    
    def from_page(self, page: dict) -> dict:
        """
        Retrieve data from a page
        """
        data = {}
        
        data['id'] = page['id'] 
        
        page_props = page["properties"]

        for key, prop in self.properties.items():
            notion_data = page_props.get(key)
            if notion_data:
                data[key] = prop.from_page_value(notion_data)
            else:
                data[key] = None
        return data
            
    def and_filter(self, simple_filters: list[dict]) -> dict:
        """
        Uses the Filter class logic.
        Combines a list of simple filter dictionaries with a logical 'and'.
        """
        return self.F.AND(simple_filters)

    def or_filter(self, simple_filters: list[dict]) -> dict:
        """
        Uses the Filter class logic.
        Combines a list of simple filter dictionaries with a logical 'or'.
        """
        return self.F.OR(simple_filters)
