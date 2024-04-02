import json
from typing import Any

from pydantic import Field, computed_field
from pyld import jsonld
from rdflib import RDF, RDFS, SDO, Graph

from ladb_data.models.base import LABaseModel, LAIri, LALiteral
from ladb_data.namespaces import RCT, ROAD, CN


class LabelledIri(LAIri):
    label: str = Field(..., alias=RDFS.label)


class Part(LABaseModel):
    type: str = Field(..., alias=SDO.additionalType)
    value: str | LabelledIri | LAIri = Field(..., alias=RDF.value)

    @computed_field
    def form_value_label(self) -> str:
        if isinstance(self.value, str):
            return self.value

        return self.value.label


class RoadLabel(LABaseModel):
    label: str = Field(..., alias=RDFS.label)
    type: str | list[str] = Field([str(ROAD.RoadLabel), str(CN.CompoundName)], alias="@type")
    has_part: list[Part] = Field(alias=SDO.hasPart)

    @computed_field
    def road_name(self) -> Part:
        item = next(part for part in self.has_part if part.type == str(RCT.RoadName))
        return item

    @computed_field
    def road_type(self) -> Part | None:
        try:
            item = next(
                part for part in self.has_part if part.type == str(RCT.RoadType)
            )
            return item
        except StopIteration:
            return None

    @computed_field
    def road_suffix(self) -> Part | None:
        try:
            item = next(
                part for part in self.has_part if part.type == str(RCT.RoadSuffix)
            )
            return item
        except StopIteration:
            return None

    def model_dump(self, *args, **kwargs) -> dict[str, Any]:
        frame = {
            "@context": {
                "https://schema.org/additionalType": {
                    "@type": "@id"
                },
                "http://www.w3.org/2000/01/rdf-schema#label": {
                    "@type": "http://www.w3.org/2001/XMLSchema#string"
                }
            },
            "@type": "https://linked.data.gov.au/def/roads/RoadLabel",
        }

        doc = super().model_dump(round_trip=True)
        framed = jsonld.frame(doc, frame)
        return framed

    def model_dump_str(self) -> str:
        return json.dumps(self.model_dump(), indent=2)

    def model_dump_graph(self) -> Graph:
        return Graph().parse(data=self.model_dump_str(), format="application/ld+json")


class SirIdentifier(LALiteral):
    type: str = Field("urn:ladb:sir-id", alias="@type")


class RoadObject(LABaseModel):
    sir_identifier: SirIdentifier = Field(..., alias=SDO.identifier)
    type: str | list[str] = Field(str(ROAD.RoadObject), alias="@type")
    label: str | RoadLabel | None = Field(None, alias=SDO.name)
    is_part_of: str | None = Field(None, alias=SDO.isPartOf)

    def model_dump(self, *args, **kwargs) -> dict[str, Any]:
        frame = {
            "@context": {
                "https://schema.org/additionalType": {
                    "@type": "@id"
                },
                "https://schema.org/isPartOf": {
                    "@type": "@id"
                },
                "https://schema.org/name": {
                    "@type": "@id"
                }
            },
            "@type": "https://linked.data.gov.au/def/roads/RoadObject",
        }

        doc = super().model_dump(round_trip=True)
        framed = jsonld.frame(doc, frame)
        return framed

    def model_dump_str(self) -> str:
        return json.dumps(self.model_dump(), indent=2)

    def model_dump_graph(self) -> Graph:
        return Graph().parse(data=self.model_dump_str(), format="application/ld+json")
