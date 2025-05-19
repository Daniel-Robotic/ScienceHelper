from bs4 import BeautifulSoup
import requests


class NomenclatureParser:
    """Parser for extracting specialty categories and subcategories from a web-based HTML table.

    This class is designed to download and parse a nomenclature table from a specified URL
    and convert it into a structured list of dictionaries.

    Attributes:
        timeout (int): Timeout in seconds for HTTP requests.
    """

    def __init__(self, timeout: int = 60):
        """Initialize the parser with a specified request timeout.

        Args:
            timeout (int, optional): Timeout in seconds for HTTP requests. Defaults to 60.
        """
        self.timeout = timeout

    def get_specialties(self, url: str) -> list[dict]:  # noqa: C901
        """Parse the HTML page from the given URL to extract specialties structure.

        The expected structure is a table with merged cells (rowspan) representing
        category names, subcategories, and nested specialty values.

        Args:
            url (str): The URL of the page containing the HTML table.

        Returns:
            list[dict]: A list of dictionaries representing categories with subcategories
                        and their associated values. Example structure:
                        [
                            {
                                "category_name": "Engineering Sciences",
                                "sub_category": [
                                    {
                                        "subcategory_name": "Mechanical Engineering",
                                        "values": ["2.1.1", "2.1.2"]
                                    },
                                    ...
                                ]
                            },
                            ...
                        ]

        Notes:
            - Returns an empty list if the request fails or the table is not found.
            - The parser assumes a specific structure with 2 to 4 columns per row.
        """
        r = requests.get(url=url, timeout=self.timeout, verify=False)
        if r.status_code != 200:  # noqa: PLR2004
            return []

        output = []
        current_main, current_sub = None, None

        soup = BeautifulSoup(r.text, "html.parser")
        table = soup.find("table")
        if not table:
            return []

        rows = table.find_all("tr")
        for row in rows[1:]:
            cells = row.find_all("td")
            if not cells:
                continue

            if len(cells) == 4:  # noqa: PLR2004
                if cells[0].has_attr("rowspan"):
                    current_main = cells[0].get_text(strip=True)
                    output.append({"category_name": current_main, "sub_category": []})
                if cells[1].has_attr("rowspan"):
                    current_sub = cells[1].get_text(strip=True)
                    output[-1]["sub_category"].append(
                        {"subcategory_name": current_sub, "values": [cells[2].get_text(strip=True)]}
                    )
                else:
                    output[-1]["sub_category"][-1]["values"].append(cells[2].get_text(strip=True))

            elif len(cells) == 3:  # noqa: PLR2004
                if cells[0].has_attr("rowspan"):
                    current_sub = cells[0].get_text(strip=True)
                    output[-1]["sub_category"].append(
                        {"subcategory_name": current_sub, "values": [cells[1].get_text(strip=True)]}
                    )
                else:
                    output[-1]["sub_category"][-1]["values"].append(cells[1].get_text(strip=True))

            elif len(cells) == 2:  # noqa: PLR2004
                output[-1]["sub_category"][-1]["values"].append(cells[0].get_text(strip=True))

        return output
