import abc
import json
import logging
from pathlib import PosixPath

import click
import requests

logger = logging.getLogger(__name__)
DEFAULT_CREDENTIALS_PATH = PosixPath(__file__).parent.parent.parent / ".credentials"


class BaseApi(abc.ABC):
    def __init__(self,
                 credentials_path: PosixPath = DEFAULT_CREDENTIALS_PATH,
                 base_url: str = "https://crew.mcaonlinecourses.com") -> None:
        self._credentials_path = credentials_path
        self._base_url = base_url
        self._session = requests.Session()
        self._session.headers["User-Agent"] = (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/149.0.0.0 Safari/537.36"
        )

        if creds := self._load_credentials():
            self._session.cookies.update(creds)

    def _load_credentials(self) -> dict | None:
        if self._credentials_path.is_file():
            return json.loads(self._credentials_path.read_text())
        return None

    def _save_credentials(self) -> None:
        self._credentials_path.write_text(json.dumps({c.name: c.value for c in self._session.cookies}))


class CrewApi(BaseApi):
    def have_valid_login(self) -> bool:
        r = self._session.get(f"{self._base_url}/api/me")
        if r.status_code == 200:
            try:
                data = r.json()
            except ValueError:
                return False
            else:
                return 'id' in data
        return False

    def perform_interactive_login(self) -> bool:
        email = click.prompt("Email")
        password = click.prompt("Password", hide_input=True)
        r = self._session.post(f"{self._base_url}/login", data={"email": email, "password": password},
                               allow_redirects=False)
        if r.status_code == 302 and r.headers.get('Location') == '/dashboard':
            print(r.headers)
            self._save_credentials()
            return True
        return False

    def fetch_active_courses(self) -> list[dict]:
        r = self._session.get(f"{self._base_url}/api/me/courses")
        r.raise_for_status()
        return [c for c in r.json()["courses"] if c["status"] == "active"]

    def fetch_course_outline(self, course_type: str) -> list[dict]:
        r = self._session.get(f"{self._base_url}/api/courses/{course_type}/outline")
        r.raise_for_status()
        return r.json()["modules"]

    def download_lms_file(self, document_id: int) -> bytes:
        r = self._session.get(f"{self._base_url}/lms-doc/{document_id}")
        r.raise_for_status()
        return r.content
