import os

import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from pathvalidate import sanitize_filename, sanitize_filepath
from urllib.parse import unquote, urlsplit


def get_response_from_link(link: str) -> requests.models.Response:
    link_response = requests.get(link, verify=False, allow_redirects=False)
    link_response.raise_for_status()
    return link_response


def write_image_to_file(data: bytes, filepath: str) -> str:
    with open(filepath, "wb") as file:
        file.write(data)


def download_image(
    image_link: str, image_filename: str, image_folder: str = "./"
) -> str:
    sanitized_folder = sanitize_filepath(image_folder)
    sanitized_filename = sanitize_filename(image_filename)
    filepath = os.path.join(sanitized_folder, sanitized_filename)
    image_data = get_response_from_link(image_link)
    write_image_to_file(image_data.content, filepath)
    return filepath


def get_image_name(image_link: str) -> str:
    image_link_parse = urlsplit(image_link)
    image_path = unquote(image_link_parse.path)
    directory_path, filename = os.path.split(image_path)
    return filename


def main():
    requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
    xkcd_json_link = "https://xkcd.com/info.0.json"
    response_json = get_response_from_link(xkcd_json_link)
    content_json = response_json.json()
    xkcd_image_link = content_json["img"]
    xkcd_image_name = get_image_name(xkcd_image_link)
    xkcd_comment = content_json["alt"]
    filepath = download_image(xkcd_image_link, xkcd_image_name)
    print(filepath, xkcd_comment)


if __name__ == "__main__":
    main()
