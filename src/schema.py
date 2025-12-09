from .properties import *
from .filters import Filter

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

        PropClass = PropertyTypes.get_property_class(t)
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
            props.update(prop.value(value))
    
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