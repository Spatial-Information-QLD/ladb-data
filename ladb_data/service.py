import urllib.parse

import httpx


class LadbDataService:
    def __init__(
            self,
            username: str,
            password: str,
            referer: str,
            auth_url: str = "https://qportal.information.qld.gov.au/arcgis/sharing/rest/generateToken",
            format_: str = "json",
            expiration_in_min: str = "60",
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

    def get_road_segments_by_name(self, name: str) -> list[dict]:
        name = urllib.parse.quote_plus(name)
        data_url = f"https://qportal.information.qld.gov.au/arcgis/rest/services/LOC/Queensland_Roads_and_Tracks/FeatureServer/0/query?where=road_name_full%3D+%27{name}%27+or+alias_1_name_full+%3D+%27{name}%27&objectIds=&time=&geometry=&geometryType=esriGeometryEnvelope&inSR=&spatialRel=esriSpatialRelIntersects&distance=&units=esriSRUnit_Foot&relationParam=&outFields=%22road_id%22%2C%22segment_id%22%2C%22road_name_full%22%2C%22alias_1_name_full%22%2C%22lga_name_left%22%2C%22lga_name_right%22%2C%22locality_right%22%2C%22locality_left%22&returnGeometry=true&maxAllowableOffset=&geometryPrecision=&outSR=&havingClause=&gdbVersion=&historicMoment=&returnDistinctValues=false&returnIdsOnly=false&returnCountOnly=false&returnExtentOnly=false&orderByFields=&groupByFieldsForStatistics=&outStatistics=&returnZ=false&returnM=false&multipatchOption=xyFootprint&resultOffset=&resultRecordCount=&returnTrueCurves=false&returnExceededLimitFeatures=false&quantizationParameters=&returnCentroid=false&timeReferenceUnknownClient=false&sqlFormat=none&resultType=&featureEncoding=esriDefault&datumTransformation=&f=pjson"

        response = httpx.get(data_url + f"&token={self.access_token}", timeout=self.timeout_in_sec)
        response.raise_for_status()

        data = response.json()
        rows = data["features"]

        # Flatten objects
        rows = [{**row['attributes'], 'geometry_paths': row['geometry']['paths']} for row in rows]
        return rows
