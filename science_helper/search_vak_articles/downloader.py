import configparser
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from fake_useragent import UserAgent
import requests

from science_helper.search_vak_articles.pdf_parser import save_to_json


class PDFDownloader:
    """Class for downloading PDF files and fetching JSON data from the web.

    This class supports:
    - Downloading a PDF file from a URL if it does not already exist.
    - Automatically updating a configuration file with the latest downloaded filename.
    - Fetching JSON data from a URL and saving it to a local `.json` file.
    """

    def __init__(self, output_dir: str = ".", config_path: str = "config.ini", timeout: int = 60):
        """Initialize the PDF downloader instance.

        Args:
            output_dir (str): Directory where files will be saved. Defaults to the current directory.
            config_path (str): Path to the configuration INI file. Defaults to "config.ini".
            timeout (int): Timeout in seconds for HTTP requests. Defaults to 60.
        """  # noqa: E501
        self.output_dir = Path(output_dir)
        self.config_path = config_path
        self.timeout = timeout

    def download_pdf_if_needed(self, url: str) -> Path:
        """Download a PDF file from the URL if it is not already downloaded.

        The URL must contain a `?name=...` parameter that specifies the filename.
        If the file already exists, it will not be downloaded again.
        The method also updates the `[DIRECTORY]` section in the configuration file with the new filename.

        Args:
            url (str): A URL pointing to a downloadable PDF, containing a `name` query parameter.

        Returns:
            Path: Path to the downloaded or existing PDF file.

        Raises:
            ValueError: If the `name` parameter is missing in the URL.
            requests.HTTPError: If the HTTP request fails.
        """  # noqa: E501
        parsed = urlparse(url)
        params = parse_qs(parsed.query)
        name = params.get("name", [None])[0]
        if not name:
            raise ValueError("URL не содержит параметра ?name=...")

        filename = f"{name}.pdf"
        filepath = self.output_dir / filename

        if filepath.exists():
            print(f"[✓] Файл уже существует: {filepath}")
        else:
            headers = {"User-Agent": UserAgent(os="Linux").random}
            resp = requests.get(url, headers=headers, timeout=self.timeout, verify=False)
            resp.raise_for_status()
            filepath.write_bytes(resp.content)
            print(f"[↓] Скачано: {filepath}")

        config = configparser.ConfigParser()
        config.read(self.config_path, encoding="utf-8")
        config["DIRECTORY"]["filename"] = filename
        with open(self.config_path, "w", encoding="utf-8") as f:
            config.write(f)

        return filepath

    def dict_from_web(self, url: str, output_file: str) -> None:
        """Fetch JSON data from the given URL and save it to a `.json` file.

        Args:
            url (str): A URL that returns JSON content.
            output_file (str): Filename for the output JSON file. ".json" extension will be appended if missing.

        Raises:
            requests.RequestException: If the request fails or times out.
        """  # noqa: E501
        if not output_file.endswith(".json"):
            output_file += ".json"

        r = requests.get(url, timeout=self.timeout, verify=False)
        if r.status_code == 200:  # noqa: PLR2004
            save_to_json(r.json(), self.output_dir / output_file)
