from rdflib import URIRef
from rdflib.namespace import DefinedNamespace, Namespace


class CN(DefinedNamespace):
    _NS = Namespace("https://linked.data.gov.au/def/cn/")
    _fail = True

    CompoundName: URIRef


class RCT(DefinedNamespace):
    _NS = Namespace("https://linked.data.gov.au/def/roads/ct/")
    _fail = True

    RoadName: URIRef
    RoadType: URIRef
    RoadSuffix: URIRef


class ROAD(DefinedNamespace):
    _NS = Namespace("https://linked.data.gov.au/def/roads/")
    _fail = True

    RoadLabel: URIRef
    RoadObject: URIRef
    RoadSegment: URIRef
