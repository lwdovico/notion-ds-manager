import os
import time
import pandas as pd
from datetime import datetime
from typing import Any, Dict, List, Optional

from notion_client import Client
from .properties import SchemaTemplate, Properties

class NotionDSManager:
    """
    Holds a Notion client and manageable registry of Data Sources (DBs).
    """

    def __init__(self, token: Optional[str] = None):
        self.client = Client(
            auth=token or os.environ.get("NOTION_TOKEN"),
            notion_version="2025-09-03",
        )
        self.data_sources: Dict[str, str] = {}  # {name → id}
        self.databases: Dict[str, str] = {} # {name → id}
        self.data_templates: Dict[str, any] = {}
        
        self.discover_data_sources()

    def discover_data_sources(self) -> Dict[str, str]:
        """
        Auto-discovers all data_sources in the workspace.
        Populates self.data_sources with {title : id}.
        """

        results = self.client.search(
            filter={"property": "object", "value": "data_source"}
        )

        for ds in results.get("results", []):
            title = ds["title"][0]["plain_text"]
            self.data_sources[title] = ds["id"]
            self.databases[title] = ds["parent"]["database_id"]
            self.data_templates[title] = SchemaTemplate(ds["properties"])
                                                    
        return results

    def get_id(self, name: str) -> str:
        return self.data_sources[name]

    def create_data_source(
            self,
            name: str,
            properties: Properties,
            parent_page_id: Optional[str] = None
        ) -> dict:
        """
        Creates a new Notion database.
        """

        assert isinstance(properties, Properties), "Properties must be provided with the Properties class builder!"
        if parent_page_id:
            parent = {"type": "page_id", "page_id": parent_page_id}
        else:
            assert os.environ.get('DEFAULT_NOTION_PAGE'), "Must provide a DEFAULT_NOTION_PAGE enviornment variable!"
            parent = {"type": "page_id", "page_id": os.environ.get('DEFAULT_NOTION_PAGE')}

        creation = self.client.databases.create(
            parent=parent,
            title=[{"type": "text", "text": {"content": name}}],
        )

        self.databases[name] = creation["id"]
        self.data_sources[name] = creation["data_sources"][0]['id']

        update = self.client.data_sources.update(data_source_id = self.data_sources[name], properties = properties.build())
        self.data_templates[name] = SchemaTemplate(update["properties"])

        response = {'db_creation' : creation, 'db_properties' : update}
        
        return response

    def create_page(
        self,
        data_source_name: str,
        properties: Dict[str, Any]
    ) -> dict:
        """
        Creates a new page inside a registered data source.
        """

        ds_id = self.get_id(data_source_name)

        response = self.client.pages.create(
            parent={"data_source_id": ds_id},
            properties=self.data_templates[data_source_name].to_page(properties)
        )

        return response

    def update_page(
        self,
        data_source_name: str,
        page_id: str,
        properties: Dict[str, Any]
    ) -> dict:
        """
        Update a page inside a registered data source.
        """
        
        response = self.client.pages.update(page_id=page_id,
                                            properties=self.data_templates[data_source_name].to_page(properties)
                                           )
        
    def query_pages(
        self,
        data_source_name: str,
        filters: Optional[List[Dict[str, Any]]] = None,
        filter_type: str = 'and',
        sorts: list = [], # raw syntax for the moment, no adaptation
        max_requests: int = None,
        page_size: int = 100,
    ) -> List[dict]:
        """
        Retrieves ALL pages from a data source, using automatic pagination.
        If a filter is provided, it will be applied.
        """
        
        ds_id = self.get_id(data_source_name)

        results = []
        cursor = None
        has_more = True

        over_requests = lambda : False if max_requests is None \
                                      else (len(results) / page_size) >= max_requests
        
        while has_more and not over_requests():
            body = {"page_size": page_size}
            if cursor:
                body["start_cursor"] = cursor
            if filters:
                assert isinstance(filters, list), "Filters are a list of dictionaries, wrap your filter into a list!"
                if filter_type == 'and':
                    body["filter"] = self.data_templates[data_source_name].and_filter(filters)
                elif filter_type == 'or':
                    body["filter"] = self.data_templates[data_source_name].or_filter(filters)
            if sorts:
                assert isinstance(sorts, list), "Sorts are a list of dictionaries, wrap your sorts into a list!"
                body["sorts"] = sorts

            response = self.client.request(
                method="post",
                path=f"data_sources/{ds_id}/query",
                body=body,
            )

            results.extend(response.get("results", []))
            cursor = response.get("next_cursor", None)
            has_more = response.get("has_more", False)

        return [self.data_templates[data_source_name].from_page(page) for page in results]
