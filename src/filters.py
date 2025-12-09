class Filter:
    """
    A class to construct complex Notion API filter objects, defaulting to 
    compound AND/OR logic for simple dictionary inputs.

    Supporting FilterCondition objects.
    """

    def __init__(self, schema_template):
        self._schema = schema_template

    def _build_condition(self, prop, condition: "FilterCondition"):
        """
        Convert a FilterCondition into a Notion filter block.
        Example:
            Status: Equals("Done")
        becomes:
            {"property": "Status", "status": {"equals": "Done"}}
        """
        value = condition.value
        operator = condition.operator
        notion_prop_type = prop.schema_key

        return {
            "property": prop.name,
            notion_prop_type: {
                operator: value
            }
        }

    def _get_prop_filter(self, prop_name: str, value: any) -> dict:
        """
        Delegates simple values to Property.to_notion_filter,
        and FilterCondition values to our internal builder.
        """
        prop = self._schema.properties.get(prop_name)
        if not prop:
            raise KeyError(f"Property '{prop_name}' not found in schema for filtering.")

        # Operator-based filtering
        if isinstance(value, FilterCondition):
            return self._build_condition(prop, value)

        return prop.to_notion_filter(value)

    def _create_and_block(self, simple_filter: dict) -> dict:
        """
        Convert a multi-key dictionary into a Notion AND block.
        Example:
            {"Status": "Done", "Priority": "High"}
        ⟶
            {"and": [ {"Status": {default_operator : "Done"}}, {"Priority": {default_operator : "High"}} ]}
        """
        if not simple_filter:
            return {}

        filters = [
            self._get_prop_filter(prop_name, value)
            for prop_name, value in simple_filter.items()
        ]

        if len(filters) == 1:
            return filters[0]

        return {"and": filters}

    def AND(self, filters: dict | list[dict]) -> dict:
        """
        Applies a logical AND.
        Input: A single multi-key dict (treated as one AND block) 
               OR a list of multi-key dicts (treated as (x) AND (y)).
        """
        if isinstance(filters, dict):
            return self._create_and_block(filters)

        if isinstance(filters, list):
            blocks = [self._create_and_block(f) for f in filters]
            blocks = [b for b in blocks if b]  # remove empty blocks

            if len(blocks) == 1:
                return blocks[0]
            if not blocks:
                return {}

            return {"and": blocks}

        raise TypeError("AND expects a dict or list[dict].")

    def OR(self, filters: dict | list[dict]) -> dict:
        """
        Applies a logical OR.
        Input: A single multi-key dict (treated as one AND block) 
               OR a list of multi-key dicts (treated as (x) OR (yf)).
        """
        if isinstance(filters, dict):
            return self._create_and_block(filters)

        if isinstance(filters, list):
            blocks = [self._create_and_block(f) for f in filters]
            blocks = [b for b in blocks if b]

            if len(blocks) == 1:
                return blocks[0]
            if not blocks:
                return {}

            return {"or": blocks}

        raise TypeError("OR expects a dict or list[dict].")

class FilterCondition:
    operator = None
    def __init__(self, value=None):
        self.value = value

class Equals(FilterCondition):             operator = "equals"
class DoesNotEqual(FilterCondition):       operator = "does_not_equal"
class Contains(FilterCondition):           operator = "contains"
class DoesNotContain(FilterCondition):     operator = "does_not_contain"
class StartsWith(FilterCondition):         operator = "starts_with"
class EndsWith(FilterCondition):           operator = "ends_with"
class GreaterThan(FilterCondition):        operator = "greater_than"
class LessThan(FilterCondition):           operator = "less_than"
class GreaterEquals(FilterCondition):      operator = "greater_than_or_equal_to"
class LessEquals(FilterCondition):         operator = "less_than_or_equal_to"
class Before(FilterCondition):             operator = "before"
class After(FilterCondition):              operator = "after"
class OnOrBefore(FilterCondition):         operator = "on_or_before"
class OnOrAfter(FilterCondition):          operator = "on_or_after"

class IsEmpty(FilterCondition):
    def __init__(self):
        super().__init__(True)
    operator = "is_empty"

class IsNotEmpty(FilterCondition):
    def __init__(self):
        super().__init__(True)
    operator = "is_not_empty"
