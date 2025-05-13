import re
import configparser

config = configparser.ConfigParser()
config.read("config.ini", encoding="utf-8")

# Регулярные выражения
RE_ROW_START = re.compile(config["REGEX"]["RE_ROW_START"], re.MULTILINE)
RE_ISSN_RAW = re.compile(config["REGEX"]["RE_ISSN_RAW"])
RE_DATE = re.compile(config["REGEX"]["RE_DATE"], re.IGNORECASE)
RE_SPEC_CODE = re.compile(config["REGEX"]["RE_SPEC_CODE"])
RE_INNER_SPACE = re.compile(config["REGEX"]["RE_INNER_SPACE"])

# Ссылки на онлайн ресурсы
WHITE_LIST_URL = config['WEB']["WHITE_LIST_URL"]
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
    config_parser = configparser.ConfigParser()

    config_parser['REGEX'] = {
        're_row_start': config['regex']['re_row_start'],
        're_issn_raw': config['regex']['re_issn_raw'],
        're_date': config['regex']['re_date'],
        're_spec_code': config['regex']['re_spec_code'],
        're_inner_space': config['regex']['re_inner_space'],
    }

    config_parser['WEB'] = {
        'white_list_url': config['web']['white_list_url'],
        'vak_list_url': config['web']['vak_list_url'],
        'SPECIALIZATION_URL': config['web']['spec_url'],
    }

    config_parser['WEB.INTERFACE'] = {
        'use_admin': str(config['admin']['enabled']),
        'admin_login': config['admin']['login'],
        'admin_password': config['admin']['password'],
    }

    config_parser['DIRECTORY'] = {
        'MAIN_DIRECTORY': config['directories']['main_dir'],
        'DATA_DIRECTORY': config['directories']['data_dir'],
        'SPECIALIZATION_NAME': config['directories']['spec_file'],
        'FILENAME': config["directories"]["file_name"]
    }

    with open('config.ini', 'w', encoding='utf-8') as configfile:
        config_parser.write(configfile)