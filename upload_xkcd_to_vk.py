import os
import pprint
from typing import Dict, List
from urllib.parse import unquote, urlsplit

import requests
from dotenv import load_dotenv
from pathvalidate import sanitize_filename, sanitize_filepath
from requests.packages.urllib3.exceptions import InsecureRequestWarning


def fetch_response(link: str, params: dict = {}) -> requests.models.Response:
    link_response = requests.get(
        link, verify=False, params=params, allow_redirects=False
    )
    link_response.raise_for_status()
    return link_response


def write_image_to_file(data: bytes, filepath: str) -> str:
    with open(filepath, "wb") as file:
        file.write(data)


def download_image(image_link: str, image_folder: str = "./") -> str:
    image_filename = get_image_name(image_link)
    sanitized_folder = sanitize_filepath(image_folder)
    sanitized_filename = sanitize_filename(image_filename)
    filepath = os.path.join(sanitized_folder, sanitized_filename)
    image_data = fetch_response(image_link)
    write_image_to_file(image_data.content, filepath)
    return filepath


def get_image_name(image_link: str) -> str:
    image_link_parse = urlsplit(image_link)
    image_path = unquote(image_link_parse.path)
    directory_path, filename = os.path.split(image_path)
    return filename


def get_vk_image_upload_url(api_link: str, params: dict) -> List:
    response_api = fetch_response(api_link, params=params)
    content_api = response_api.json()
    return content_api["response"]["upload_url"]


def upload_image_to_wall_vk_group(api_link: str, image_filepath: str) -> Dict:
    with open(image_filepath, "rb") as image_file:
        files = {
            "photo": image_file,
        }
        response_api = requests.post(api_link, files=files)
        response_api.raise_for_status()
    return response_api.json()


def save_image_to_wall_vk_group(
    api_link: str, params: dict, upload_image_params: dict
) -> Dict:
    params.update(upload_image_params)
    response_api = requests.post(api_link, params=params)
    response_api.raise_for_status()
    return response_api.json()


def publish_image_to_wall_vk_group(
    api_link: str, params: dict, save_image_response: dict, message: str
) -> Dict:
    owner_id = save_image_response["response"][0].get("owner_id")
    media_id = save_image_response["response"][0].get("id")
    params["from_group"] = "1"
    params["message"] = message
    params["attachments"] = f"photo{ owner_id }_{ media_id }"
    params["owner_id"] = f"-{ params['group_id'] }"
    response_api = requests.post(api_link, params=params)
    response_api.raise_for_status()
    return response_api.json()


def main():
    requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
    load_dotenv()
    xkcd_json_link = "https://xkcd.com/info.0.json"

    vk_get_wall_upload_upload_server_api = (
        "https://api.vk.com/method/photos.getWallUploadServer"
    )
    vk_save_wall_photo_api = "https://api.vk.com/method/photos.saveWallPhoto"
    vk_publish_wall_photo_api = "https://api.vk.com/method/wall.post"
    vk_access_token = os.getenv("VK_ACCESS_TOKEN")
    vk_group_id = os.getenv("VK_GROUP_ID")
    vk_params = {
        "access_token": vk_access_token,
        "group_id": vk_group_id,
        "v": "5.130",
    }

    response_json = fetch_response(xkcd_json_link)
    content_json = response_json.json()
    xkcd_image_link = content_json["img"]
    xkcd_comment = content_json["alt"]
    xkcd_title = content_json["title"]
    xkcd_image_filepath = download_image(xkcd_image_link)

    vk_image_upload_url = get_vk_image_upload_url(
        vk_get_wall_upload_upload_server_api, vk_params
    )
    upload_image_params = upload_image_to_wall_vk_group(
        vk_image_upload_url, xkcd_image_filepath
    )
    save_image_response = save_image_to_wall_vk_group(
        vk_save_wall_photo_api, vk_params, upload_image_params
    )
    publish_image_response = publish_image_to_wall_vk_group(
        vk_publish_wall_photo_api, vk_params, save_image_response, xkcd_title
    )
    pprint.pprint(publish_image_response)


if __name__ == "__main__":
    main()