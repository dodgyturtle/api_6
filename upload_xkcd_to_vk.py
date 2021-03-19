import os
from typing import Any, Dict, List, Optional
from urllib.parse import unquote, urlsplit

import requests
from dotenv import load_dotenv
from pathvalidate import sanitize_filename, sanitize_filepath
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from random import randrange


def fetch_random_comic(comic_current_link: str) -> List[Any]:
    current_comic_response = fetch_response(comic_current_link)
    current_comic_content = current_comic_response.json()
    comic_last_number = current_comic_content["num"]
    random_comic_number = randrange(1, comic_last_number)
    random_comic_link = f"http://xkcd.com/{ random_comic_number }/info.0.json"
    random_comic_response = fetch_response(random_comic_link)
    random_comic_content = random_comic_response.json()
    return random_comic_content["img"], random_comic_content["title"]


def fetch_response(link: str, params: dict = {}) -> requests.models.Response:
    link_response = requests.get(link, verify=False, params=params)
    link_response.raise_for_status()
    return link_response

def validate_vk_api_response(api_answer: dict) -> Optional[requests.exceptions.HTTPError]:
    if "error" in api_answer:
        raise requests.exceptions.HTTPError(api_answer["error"])


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
    api_response = fetch_response(api_link, params=params)
    api_content = api_response.json()
    validate_vk_api_response(api_content)
    return api_content["response"]["upload_url"]


def upload_image_to_vk_group_wall(api_link: str, image_filepath: str) -> Dict:
    with open(image_filepath, "rb") as image_file:
        files = {
            "photo": image_file,
        }
        try:
            api_response = requests.post(api_link, files=files)
            api_content = api_response.json()
            validate_vk_api_response(api_content)
        finally:
            os.remove(image_filepath)
    return api_content


def save_image_to_vk_group_wall(
    api_link: str, params: dict, upload_image_params: dict
) -> Dict:
    save_image_params = {}
    save_image_params.update(upload_image_params)
    save_image_params.update(params)
    api_response = requests.post(api_link, params=save_image_params)
    api_content = api_response.json()
    validate_vk_api_response(api_content)
    return api_content


def publish_image_to_vk_group_wall(
    api_link: str, params: dict, owner_id: str, media_id: str, message: str
) -> Dict:
    publish_image_params = {
        "from_group": "1",
        "message": message,
        "attachments": f"photo{ owner_id }_{ media_id }",
        "owner_id": f"-{ params['group_id'] }",
    }
    publish_image_params.update(params)
    api_response = requests.post(api_link, params=publish_image_params)
    api_response.raise_for_status()
    return api_response.json()


def main():
    requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
    load_dotenv()
    xkcd_current_comic_link = "https://xkcd.com/info.0.json"
    vk_get_wall_upload_server_api = \
        "https://api.vk.com/method/photos.getWallUploadServer"
    
    vk_save_wall_photo_api = "https://api.vk.com/method/photos.saveWallPhoto"
    vk_publish_wall_photo_api = "https://api.vk.com/method/wall.post"
    vk_access_token = os.getenv("VK_ACCESS_TOKEN")
    vk_group_id = os.getenv("VK_GROUP_ID")
    vk_params = {
        "access_token": vk_access_token,
        "group_id": vk_group_id,
        "v": "5.130",
    }
    try:
        comic_img, comic_title = fetch_random_comic(xkcd_current_comic_link)
        comic_image_filepath = download_image(comic_img)
        vk_image_upload_url = get_vk_image_upload_url(
            vk_get_wall_upload_server_api, vk_params
        )
        vk_upload_image_params = upload_image_to_vk_group_wall(
            vk_image_upload_url, comic_image_filepath
        )
        vk_save_image_response = save_image_to_vk_group_wall(
            vk_save_wall_photo_api, vk_params, vk_upload_image_params
        )
        vk_image_owner_id = vk_save_image_response["response"][0].get("owner_id")
        vk_image_media_id = vk_save_image_response["response"][0].get("id")
        publish_image_to_vk_group_wall(
            vk_publish_wall_photo_api,
            vk_params,
            vk_image_owner_id,
            vk_image_media_id,
            comic_title,
        )
    except (
        requests.exceptions.ConnectionError,
        requests.exceptions.HTTPError,
    ) as error:
        print(f"Произошла ошибка: { error }")


if __name__ == "__main__":
    main()
