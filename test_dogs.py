import random
import pytest
import requests


class YaUploader:
    def __init__(self):
        pass

    def create_folder(self, path, token):
        url_create = 'https://cloud-api.yandex.net/v1/disk/resources'
        headers = {'Content-Type': 'application/json', 'Accept': 'application/json', 'Authorization': f'OAuth {token}'}
        response = requests.put(f'{url_create}?path={path}', headers=headers)
        if response.status_code == 201:
            print(f"Folder '{path}' created successfully.")
        elif response.status_code == 409:
            print(f"Folder '{path}' already exists.")
        else:
            raise Exception(f"Failed to create folder: {response.status_code} {response.text}")
        return response

    def upload_photos_to_yd(self, token, path, url_file, name):
        url = "https://cloud-api.yandex.net/v1/disk/resources/upload"
        headers = {'Content-Type': 'application/json', 'Accept': 'application/json', 'Authorization': f'OAuth {token}'}
        params = {"path": f'/{path}/{name}', 'url': url_file, "overwrite": "true"}
        response = requests.post(url, headers=headers, params=params)
        if response.status_code != 202:
            raise Exception(f"Failed to upload file: {response.status_code} {response.text}")
        return response


def get_sub_breeds(breed):
    res = requests.get(f'https://dog.ceo/api/breed/{breed}/list')
    if res.status_code != 200:
        raise Exception(f"Failed to get sub-breeds: {res.status_code} {res.text}")
    return res.json().get('message', [])


def get_urls(breed, sub_breeds):
    url_images = []
    if sub_breeds:
        for sub_breed in sub_breeds:
            res = requests.get(f"https://dog.ceo/api/breed/{breed}/{sub_breed}/images/random")
            if res.status_code == 200:
                url_images.append(res.json().get('message'))
            else:
                print(f"Failed to get image for sub-breed {sub_breed}: {res.status_code}")
    else:
        res = requests.get(f"https://dog.ceo/api/breed/{breed}/images/random")
        if res.status_code == 200:
            url_images.append(res.json().get('message'))
        else:
            print(f"Failed to get image for breed {breed}: {res.status_code}")
    return url_images


def u(breed):
    sub_breeds = get_sub_breeds(breed)
    urls = get_urls(breed, sub_breeds)
    yandex_client = YaUploader()
    yandex_client.create_folder('test_folder', "AgAAAAAJtest_tokenxkUEdew")
    for url in urls:
        part_name = url.split('/')
        name = '_'.join([part_name[-2], part_name[-1]])
        yandex_client.upload_photos_to_yd("AgAAAAAJtest_tokenxkUEdew", "test_folder", url, name)


@pytest.mark.parametrize('breed', ['doberman', 'bulldog', 'collie'])
def test_proverka_upload_dog(breed):
    breed = random.choice(['doberman', 'bulldog', 'collie'])  # Перемещаем рандомизацию внутрь теста
    u(breed)

    # Проверка
    url_create = 'https://cloud-api.yandex.net/v1/disk/resources'
    headers = {'Content-Type': 'application/json', 'Accept': 'application/json', 'Authorization': f'OAuth AgAAAAAJtest_tokenxkUEdew'}
    response = requests.get(f'{url_create}?path=/test_folder', headers=headers)
    assert response.status_code == 200, f"Failed to fetch folder info: {response.status_code}"
    
    folder_info = response.json()
    assert folder_info['type'] == "dir", "Folder is not of type 'dir'"
    assert folder_info['name'] == "test_folder", "Folder name is incorrect"

    if get_sub_breeds(breed) == []:
        assert len(folder_info['_embedded']['items']) == 1, "Incorrect number of items in folder"
        for item in folder_info['_embedded']['items']:
            assert item['type'] == 'file', "Item is not a file"
            assert item['name'].startswith(breed), "File name does not start with breed name"
    else:
        assert len(folder_info['_embedded']['items']) == len(get_sub_breeds(breed)), "Incorrect number of files for sub-breeds"
        for item in folder_info['_embedded']['items']:
            assert item['type'] == 'file', "Item is not a file"
            assert item['name'].startswith(breed), "File name does not start with breed name"
