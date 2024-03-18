import json
from typing import Any, Optional

import httpx
import pyshacl
import rfc3987
from pydantic import BaseModel, ConfigDict, Field, field_validator
from rdflib import SDO, Graph


class LABaseModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="allow")

    id: str = Field(alias="@id")
    context: Optional[dict] = Field(None, alias="@context", exclude=True)

    @field_validator("id")
    @classmethod
    def validate_iri(cls, v: str) -> str:
        if not rfc3987.match(v, "IRI") and not v.startswith("_:"):
            raise ValueError(
                f"Value '{v}' does not conform to RFC 3987 - Internationalized Resource Identifiers (IRIs)."
            )
        return v

    def model_dump(self, *args, **kwargs) -> dict[str, Any]:
        return super().model_dump(by_alias=True, *args, **kwargs)

    def model_dump_trig(self, named_graph: str, content_type: str):
        data = {"@context": self.context, **self.model_dump()}
        data_str = json.dumps(data)
        graph = Graph(identifier=named_graph).parse(
            data=data_str, format="application/ld+json"
        )

        # TODO: Move validation to on model creation
        # TODO: Timed cache in Redis to avoid making http request every time.
        if hasattr(self, "schema_version"):
            response = httpx.get(self.schema_version)
            shacl = response.text

            # TODO: Improve this...
            # Merge shacl content with data graph since shacl content contains some vocabs required for validation.
            data_graph = Graph().parse(
                data=json.dumps(data), format="application/ld+json"
            )
            data_graph.parse(data=shacl)

            shacl_graph = Graph().parse(data=shacl)
            conforms, results_graph, results_text = pyshacl.validate(
                data_graph, shacl_graph=shacl_graph
            )
            if not conforms:
                raise ValueError(results_text)

        return graph.serialize(format=content_type)


class LABaseWithType(LABaseModel):
    type: list[str] | str = Field(alias="@type")
    schema_version: str = Field(
        ...,
        alias=SDO.schemaVersion,
    )


class LAIri(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="allow")

    id: str = Field(..., alias="@id")


class LALiteral(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="allow")

    value: str = Field(..., alias="@value")
    type: str = Field("http://www.w3.org/2001/XMLSchema#string", alias="@type")
