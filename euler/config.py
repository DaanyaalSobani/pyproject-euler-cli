from pathlib import Path
import keyring as _keyring

BASE_URL = "https://projecteuler.net"
SESSION_FILE = Path.home() / ".euler" / "session.json"
KEYRING_SERVICE = "euler-cli"
KEYRING_USERNAME_KEY = "__euler_username__"
DEV_ENV_PATH = Path(__file__).parent.parent / "dev.env"


def load_dev_env() -> dict[str, str]:
    if not DEV_ENV_PATH.exists():
        return {}
    result: dict[str, str] = {}
    for line in DEV_ENV_PATH.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, _, value = line.partition("=")
            result[key.strip()] = value.strip()
    return result


def get_credentials() -> tuple[str, str] | None:
    dev = load_dev_env()
    if "EULER_USERNAME" in dev and "EULER_PASSWORD" in dev:
        return dev["EULER_USERNAME"], dev["EULER_PASSWORD"]
    username = _keyring.get_password(KEYRING_SERVICE, KEYRING_USERNAME_KEY)
    if not username:
        return None
    password = _keyring.get_password(KEYRING_SERVICE, username)
    return (username, password) if password else None


def save_credentials(username: str, password: str) -> None:
    _keyring.set_password(KEYRING_SERVICE, KEYRING_USERNAME_KEY, username)
    _keyring.set_password(KEYRING_SERVICE, username, password)


def delete_credentials() -> None:
    username = _keyring.get_password(KEYRING_SERVICE, KEYRING_USERNAME_KEY)
    if username:
        for key in (username, KEYRING_USERNAME_KEY):
            try:
                _keyring.delete_password(KEYRING_SERVICE, key)
            except Exception:
                pass
