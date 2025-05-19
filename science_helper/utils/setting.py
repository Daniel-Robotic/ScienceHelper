import configparser
from pathlib import Path
import re


# Путь до конфигурационного файла
CONFIG_PATH = Path("config.ini")

# Чтение конфигурации
config = configparser.ConfigParser()
config.read(CONFIG_PATH, encoding="utf-8")

# Регулярные выражения
RE_ROW_START = re.compile(config["REGEX"]["RE_ROW_START"], re.MULTILINE)
RE_ISSN_RAW = re.compile(config["REGEX"]["RE_ISSN_RAW"])
RE_DATE = re.compile(config["REGEX"]["RE_DATE"], re.IGNORECASE)
RE_SPEC_CODE = re.compile(config["REGEX"]["RE_SPEC_CODE"])
RE_INNER_SPACE = re.compile(config["REGEX"]["RE_INNER_SPACE"])

# Ссылки на онлайн ресурсы
WHITE_LIST_URL = config["WEB"]["WHITE_LIST_URL"]
VAK_LIST_URL = config["WEB"]["VAK_LIST_URL"]
SPECIALIZATION_URL = config["WEB"]["SPECIALIZATION_URL"]

# Настройки админ панели
USE_ADMIN = config["WEB.INTERFACE"]["use_admin"]
ADMIN_LOGIN = config["WEB.INTERFACE"]["admin_login"]
ADMIN_PASSWORD = config["WEB.INTERFACE"]["admin_password"]

# Настройки директории
MAIN_DIRECTORY = config["DIRECTORY"]["MAIN_DIRECTORY"]
DATA_DIRECTORY = config["DIRECTORY"]["DATA_DIRECTORY"]
SPECIALIZATION_NAME = config["DIRECTORY"]["SPECIALIZATION_NAME"]
FILENAME = config["DIRECTORY"]["filename"]


def save_config(config):
    """Save the provided configuration dictionary to an INI file.

    The function writes structured configuration data into an INI file,
    organizing it into sections such as REGEX, WEB, WEB.INTERFACE, and DIRECTORY.

    Args:
        config (dict): A nested dictionary containing configuration values.
            Expected structure:
                {
                    "regex": {
                        "re_row_start": str,
                        "re_issn_raw": str,
                        "re_date": str,
                        "re_spec_code": str,
                        "re_inner_space": str
                    },
                    "web": {
                        "white_list_url": str,
                        "vak_list_url": str,
                        "spec_url": str
                    },
                    "admin": {
                        "enabled": bool,
                        "login": str,
                        "password": str
                    },
                    "directories": {
                        "main_dir": str,
                        "data_dir": str,
                        "spec_file": str,
                        "file_name": str
                    }
                }

    Raises:
        KeyError: If any of the expected keys are missing from the config.
        OSError: If writing to the configuration file fails.
    """
    config_parser = configparser.ConfigParser()

    config_parser["REGEX"] = {
        "re_row_start": config["regex"]["re_row_start"],
        "re_issn_raw": config["regex"]["re_issn_raw"],
        "re_date": config["regex"]["re_date"],
        "re_spec_code": config["regex"]["re_spec_code"],
        "re_inner_space": config["regex"]["re_inner_space"],
    }

    config_parser["WEB"] = {
        "white_list_url": config["web"]["white_list_url"],
        "vak_list_url": config["web"]["vak_list_url"],
        "SPECIALIZATION_URL": config["web"]["spec_url"],
    }

    config_parser["WEB.INTERFACE"] = {
        "use_admin": str(config["admin"]["enabled"]),
        "admin_login": config["admin"]["login"],
        "admin_password": config["admin"]["password"],
    }

    config_parser["DIRECTORY"] = {
        "MAIN_DIRECTORY": config["directories"]["main_dir"],
        "DATA_DIRECTORY": config["directories"]["data_dir"],
        "SPECIALIZATION_NAME": config["directories"]["spec_file"],
        "FILENAME": config["directories"]["file_name"],
    }

    with CONFIG_PATH.open("w", encoding="utf-8") as f:
        config_parser.write(f)
