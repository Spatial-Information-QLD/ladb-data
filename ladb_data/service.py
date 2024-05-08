import urllib.parse
from datetime import date

import httpx
from rdflib import Graph, URIRef, PROV, RDF, SDO, Literal, BNode, RDFS, TIME, XSD
from rdflib.namespace import GEO

from ladb_data.namespaces import GN, CN, GNPT, LC


class LadbDataService:
    def __init__(
            self,
            username: str,
            password: str,
            referer: str,
            auth_url: str = "https://qportal.information.qld.gov.au/arcgis/sharing/rest/generateToken",
            format_: str = "json",
            expiration_in_min: str = "1",
            timeout_in_sec: int = 60,
         ):
        params = {
            "f": format_,
            "referer": referer,
            "expiration": expiration_in_min,
        }
        data = {
            "username": username,
            "password": password,
        }
        response = httpx.post(auth_url, params=params, data=data, timeout=timeout_in_sec)
        response.raise_for_status()

        access_token = response.json()["token"]

        self.timeout_in_sec = timeout_in_sec
        self.access_token = access_token

    def http_get(self, data_url: str) -> dict:
        response = httpx.get(data_url + f"&token={self.access_token}", timeout=self.timeout_in_sec)
        response.raise_for_status()
        return response.json()

    def _get_locality_by_id(self, reference_number: str) -> dict:
        reference_number_quoted = urllib.parse.quote_plus(reference_number)
        data_url = f"https://qportal.information.qld.gov.au/arcgis/rest/services/PlaceNames/Place_Names_Enquiry/FeatureServer/0/query?where=reference_number+%3D+{reference_number_quoted}&objectIds=&time=&geometry=&geometryType=esriGeometryEnvelope&inSR=&spatialRel=esriSpatialRelIntersects&distance=&units=esriSRUnit_Foot&relationParam=&outFields=*&returnGeometry=true&maxAllowableOffset=&geometryPrecision=&outSR=&havingClause=&gdbVersion=&historicMoment=&returnDistinctValues=false&returnIdsOnly=false&returnCountOnly=false&returnExtentOnly=false&orderByFields=&groupByFieldsForStatistics=&outStatistics=&returnZ=false&returnM=false&multipatchOption=xyFootprint&resultOffset=&resultRecordCount=&returnTrueCurves=false&returnExceededLimitFeatures=false&quantizationParameters=&returnCentroid=false&timeReferenceUnknownClient=false&sqlFormat=none&resultType=&featureEncoding=esriDefault&datumTransformation=&f=pjson"

        data = self.http_get(data_url)
        rows = data["features"]

        # Flatten objects
        rows = [{**row['attributes'], 'point_x': row['geometry']['x'], 'point_y': row['geometry']['y']} for row in rows]

        if not len(rows) == 1:
            raise ValueError(f"Expected one row, but got {len(rows)} for reference_number {reference_number}.")

        return rows[0]

    def _get_historical_localities(self, reference_number: str) -> list[str]:
        reference_number_quoted = urllib.parse.quote_plus(reference_number)
        data_url = f"https://qportal.information.qld.gov.au/arcgis/rest/services/PlaceNames/Place_Names_Enquiry/FeatureServer/1/query?where=reference_number+%3D+{reference_number_quoted}&objectIds=&time=&geometry=&geometryType=esriGeometryEnvelope&inSR=&spatialRel=esriSpatialRelIntersects&distance=&units=esriSRUnit_Foot&relationParam=&outFields=*&returnGeometry=true&maxAllowableOffset=&geometryPrecision=&outSR=&havingClause=&gdbVersion=&historicMoment=&returnDistinctValues=false&returnIdsOnly=false&returnCountOnly=false&returnExtentOnly=false&orderByFields=&groupByFieldsForStatistics=&outStatistics=&returnZ=false&returnM=false&multipatchOption=xyFootprint&resultOffset=&resultRecordCount=&returnTrueCurves=false&returnCentroid=false&timeReferenceUnknownClient=false&sqlFormat=none&resultType=&featureEncoding=esriDefault&datumTransformation=&f=pjson"

        data = self.http_get(data_url)
        rows = data["features"]

        return [str(row['attributes']['historic_reference_number']) for row in rows]

    def _get_indigenous_labels(self, reference_number: str) -> list[dict]:
        reference_number_quoted = urllib.parse.quote_plus(reference_number)
        data_url = f"https://qportal.information.qld.gov.au/arcgis/rest/services/PlaceNames/Place_Names_Enquiry/FeatureServer/2/query?where=reference_number+%3D+{reference_number_quoted}&objectIds=&time=&geometry=&geometryType=esriGeometryEnvelope&inSR=&spatialRel=esriSpatialRelIntersects&distance=&units=esriSRUnit_Foot&relationParam=&outFields=*&returnGeometry=true&maxAllowableOffset=&geometryPrecision=&outSR=&havingClause=&gdbVersion=&historicMoment=&returnDistinctValues=false&returnIdsOnly=false&returnCountOnly=false&returnExtentOnly=false&orderByFields=&groupByFieldsForStatistics=&outStatistics=&returnZ=false&returnM=false&multipatchOption=xyFootprint&resultOffset=&resultRecordCount=&returnTrueCurves=false&returnCentroid=false&timeReferenceUnknownClient=false&sqlFormat=none&resultType=&featureEncoding=esriDefault&datumTransformation=&f=pjson"

        data = self.http_get(data_url)
        rows = data["features"]

        return [row['attributes'] for row in rows]

    @staticmethod
    def add_additional_property(iri: URIRef, k: str, v: str, graph: Graph):
        property_value = BNode()
        graph.add((iri, SDO.additionalProperty, property_value))
        graph.add((property_value, SDO.propertyID, Literal(str(k))))
        graph.add((property_value, SDO.value, Literal(str(v))))

    @staticmethod
    def _create_locality_label( geographical_object: dict, iri: URIRef, object_iri: URIRef, graph: Graph, is_indigenous: bool = False) -> None:
        graph.add((iri, RDF.type, GN.GeographicalName))
        graph.add((iri, RDF.type, CN.CompoundName))

        label = geographical_object['place_name']
        graph.add((iri, RDFS.label, Literal(label, lang="en" if not is_indigenous else "aus")))

        identifier = geographical_object['objectid']
        graph.add((iri, SDO.identifier, Literal(identifier, datatype=URIRef("urn:ladb:sir-id"))))

        graph.add((iri, CN.isNameFor, object_iri))

        given_name_part = BNode()
        graph.add((iri, SDO.hasPart, given_name_part))
        graph.add((given_name_part, SDO.additionalType, GNPT.geographicalGivenName))
        graph.add((given_name_part, RDF.value, Literal(label)))

        lifecycle_stage = BNode()
        graph.add((iri, LC.hasLifecycleStage, lifecycle_stage))
        time_beginning = BNode()
        graph.add((lifecycle_stage, TIME.hasBeginning, time_beginning))
        graph.add((time_beginning, TIME.inXSDDate, Literal(date.today(), datatype=XSD.date)))
        # TODO: Add as submitted for now. Determine whether there's a better default status.
        graph.add((lifecycle_stage, SDO.additionalType, URIRef("https://linked.data.gov.au/def/reg-statuses/submitted")))

    def _convert_geographical_object_to_rdf(self, geographical_object: dict, table_name: str) -> Graph:
        graph = Graph()
        iri = URIRef(f"https://linked.data.gov.au/dataset/qld-addr/go/{geographical_object["reference_number"]}")
        graph.add((iri, RDF.type, GN.GeographicalObject))

        # category
        geographical_object_category = geographical_object["type"]
        if geographical_object_category == 'IS':
            graph.add((iri, SDO.additionalType, URIRef('https://linked.data.gov.au/def/go-categories/island')))
        elif geographical_object_category == 'SUB' or geographical_object_category == "LOCB":
            graph.add((iri, SDO.additionalType, URIRef('https://linked.data.gov.au/def/go-categories/locality')))
        else:
            raise ValueError(f"Unhandled geographical object category: {geographical_object['type']}")

        # identifier
        graph.add((iri, SDO.identifier, Literal(geographical_object['reference_number'], datatype=URIRef('urn:ladb:sir-id'))))

        # geometry
        geometry = BNode()
        graph.add((iri, GEO.hasGeometry, geometry))
        graph.add((geometry, GEO.asWKT, Literal(f"POINT ({geographical_object['point_x']} {geographical_object['point_y']})", datatype=GEO.wktLiteral)))

        # name
        name_iri = URIRef(f"https://linked.data.gov.au/dataset/qld-addr/gn/{geographical_object['objectid']}")
        graph.add((iri, SDO.name, name_iri))

        # additional properties
        self.add_additional_property(iri, "table", table_name, graph)
        self.add_additional_property(name_iri, "table", table_name, graph)
        for k, v in geographical_object.items():
            if v:
                if k in ['reference_number', 'type', 'plan_number', 'longitude_dd', 'latitude_dd', 'lga', 'point_x', 'point_y']:
                    self.add_additional_property(iri, k, v, graph)
                else:
                    self.add_additional_property(name_iri, k, v, graph)

        # geographical name
        # if geographical_object_category in ('SUB', 'LOCB'):
        #     self._create_locality_label(geographical_object, name_iri, iri, graph)
        # Just convert everything as a "locality" for now.
        self._create_locality_label(geographical_object, name_iri, iri, graph)

        return graph

    def get_locality_by_id(self, reference_number: str) -> Graph:
        graph = Graph()
        current_locality = self._get_locality_by_id(reference_number)
        current_locality_iri = URIRef(f"https://linked.data.gov.au/dataset/qld-addr/go/{current_locality["reference_number"]}")

        # Convert to RDF
        graph += self._convert_geographical_object_to_rdf(current_locality, "Place Name")

        # Check whether it supersedes another locality
        historical_reference_numbers = self._get_historical_localities(str(current_locality["reference_number"]))
        for historical_reference_number in historical_reference_numbers:
            historical_reference_number_iri = URIRef(f"https://linked.data.gov.au/dataset/qld-addr/go/{historical_reference_number}")

            # Add prov:wasDerivedFrom relationship
            graph.add((current_locality_iri, PROV.wasDerivedFrom, historical_reference_number_iri))

            # Recursively call get_locality_by_id for each historical reference number
            graph += self.get_locality_by_id(historical_reference_number)

        # Get indigenous names, if any
        indigenous_names = self._get_indigenous_labels(reference_number)
        # Convert to RDF
        for indigenous_name in indigenous_names:
            name_iri = URIRef(f"https://linked.data.gov.au/dataset/qld-addr/gn/{indigenous_name['objectid']}")
            self._create_locality_label(indigenous_name, name_iri, current_locality_iri, graph, is_indigenous=True)

            self.add_additional_property(name_iri, "table", "Indigenous name", graph)
            for k, v in indigenous_name.items():
                if v:
                    if k in ['reference_number', 'type', 'plan_number', 'longitude_dd', 'latitude_dd', 'lga', 'point_x',
                             'point_y']:
                        self.add_additional_property(current_locality_iri, k, v, graph)
                    else:
                        self.add_additional_property(name_iri, k, v, graph)

        return graph

    def get_road_segments_by_name(self, name: str) -> list[dict]:
        name = urllib.parse.quote_plus(name)
        data_url = f"https://qportal.information.qld.gov.au/arcgis/rest/services/LOC/Queensland_Roads_and_Tracks/FeatureServer/0/query?where=road_name_full%3D+%27{name}%27+or+alias_1_name_full+%3D+%27{name}%27&objectIds=&time=&geometry=&geometryType=esriGeometryEnvelope&inSR=&spatialRel=esriSpatialRelIntersects&distance=&units=esriSRUnit_Foot&relationParam=&outFields=%22road_id%22%2C%22segment_id%22%2C%22road_name_full%22%2C%22alias_1_name_full%22%2C%22lga_name_left%22%2C%22lga_name_right%22%2C%22locality_right%22%2C%22locality_left%22&returnGeometry=true&maxAllowableOffset=&geometryPrecision=&outSR=&havingClause=&gdbVersion=&historicMoment=&returnDistinctValues=false&returnIdsOnly=false&returnCountOnly=false&returnExtentOnly=false&orderByFields=&groupByFieldsForStatistics=&outStatistics=&returnZ=false&returnM=false&multipatchOption=xyFootprint&resultOffset=&resultRecordCount=&returnTrueCurves=false&returnExceededLimitFeatures=false&quantizationParameters=&returnCentroid=false&timeReferenceUnknownClient=false&sqlFormat=none&resultType=&featureEncoding=esriDefault&datumTransformation=&f=pjson"

        data = self.http_get(data_url)
        rows = data["features"]

        # Flatten objects
        rows = [{**row['attributes'], 'geometry_paths': row['geometry']['paths']} for row in rows]
        return rows

    def get_road_segments_by_road_id(self, road_id: str) -> list[dict]:
        name = urllib.parse.quote_plus(road_id)
        data_url = f"https://qportal.information.qld.gov.au/arcgis/rest/services/LOC/Queensland_Roads_and_Tracks/FeatureServer/0/query?where=road_id%3D+%27{name}%27&objectIds=&time=&geometry=&geometryType=esriGeometryEnvelope&inSR=&spatialRel=esriSpatialRelIntersects&distance=&units=esriSRUnit_Foot&relationParam=&outFields=%22road_id%22%2C%22segment_id%22%2C%22road_name_full%22%2C%22alias_1_name_full%22%2C%22lga_name_left%22%2C%22lga_name_right%22%2C%22locality_right%22%2C%22locality_left%22&returnGeometry=true&maxAllowableOffset=&geometryPrecision=&outSR=&havingClause=&gdbVersion=&historicMoment=&returnDistinctValues=false&returnIdsOnly=false&returnCountOnly=false&returnExtentOnly=false&orderByFields=&groupByFieldsForStatistics=&outStatistics=&returnZ=false&returnM=false&multipatchOption=xyFootprint&resultOffset=&resultRecordCount=&returnTrueCurves=false&returnExceededLimitFeatures=false&quantizationParameters=&returnCentroid=false&timeReferenceUnknownClient=false&sqlFormat=none&resultType=&featureEncoding=esriDefault&datumTransformation=&f=pjson"

        data = self.http_get(data_url)
        rows = data["features"]

        # Flatten objects
        rows = [{**row['attributes'], 'geometry_paths': row['geometry']['paths']} for row in rows]
        return rows
