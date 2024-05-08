from rdflib import URIRef
from rdflib.namespace import DefinedNamespace, Namespace


class CN(DefinedNamespace):
    _NS = Namespace("https://linked.data.gov.au/def/cn/")
    _fail = True

    CompoundName: URIRef
    isNameFor: URIRef


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


class GN(DefinedNamespace):
    _NS = Namespace("https://linked.data.gov.au/def/gn/")
    _fail = True

    GeographicalObject: URIRef
    GeographicalName: URIRef


class GNPT(DefinedNamespace):
    _NS = Namespace("https://linked.data.gov.au/def/gn-part-types/")
    _fail = True

    geographicalGivenName: URIRef


class LC(DefinedNamespace):
    _NS = Namespace("https://linked.data.gov.au/def/lifecycle/")
    _fail = True

    hasLifecycleStage: URIRef
