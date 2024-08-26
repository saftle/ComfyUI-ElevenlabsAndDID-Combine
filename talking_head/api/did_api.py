#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2024/3/14 下午1:54
# @Author  : Aliang

import os.path
import requests
import json
import time


class DiDClient(object):
    def __init__(self, authorization):
        self.authorization = authorization

    def upload_audio_file(self, file_path):
        url = "https://api.d-id.com/audios"
        file_name = os.path.basename(file_path)
        retry_delay = 5
        try_times = 3
        index = 0
        while True:
            files = {"audio": (file_name, open(file_path, "rb"), "audio/mpeg")}
            headers = {"accept": "application/json",
                       "authorization": self.authorization
                       }
            response = requests.post(url, files=files, headers=headers, timeout=30)
            if response.status_code == 201:
                audio_url = json.loads(response.text)["url"]
                return audio_url
            else:
                index = index + 1
                if index > try_times:
                    raise Exception(f"upload audio file err: the err code is {response.status_code}")
                time.sleep(retry_delay)

    def upload_image(self, file_path):
        """
        上传图片
        :return:
        """
        url = "https://api.d-id.com/images"
        file_name = os.path.basename(file_path)
        retry_delay = 5
        try_times = 3
        index = 0
        while True:
            files = {"image": (file_name, open(file_path, "rb"), "image/png")}
            headers = {
                "accept": "application/json",
                "authorization": self.authorization
            }
            response = requests.post(url, files=files, headers=headers, timeout=10)
            if response.status_code == 201:
                image_url = json.loads(response.text)['url']
                return image_url
            else:
                index = index + 1
                if index > try_times:
                    raise Exception(f"upload image file err: the err code is {response.status_code}, the file is {file_path}")
                time.sleep(retry_delay)

    def create_a_talk(self, image_url, audio_url=None):
        """
        创建一个说话
        :return:
        """
        url = "https://api.d-id.com/talks"
        payload = {
            "script": {
                "type": "audio",
                "subtitles": "false",
                "provider": {
                    "type": "microsoft",
                    "voice_id": "en-US-JennyNeural"
                },
                "audio_url": audio_url
            },
            "config": {
                "fluent": "false",
                "pad_audio": "0.0",
                "align_driver": False,
                "stitch": True
            },
            "source_url": image_url
        }
        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "authorization": self.authorization
        }

        retry_delay = 5
        try_times = 3
        index = 0
        while True:
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            if response.status_code == 201:
                task_id = json.loads(response.text)['id']
                return task_id
            else:
                index = index + 1
                if index > try_times:
                    raise Exception(f"create a talk err: the err code is {response.status_code}")
                time.sleep(retry_delay)

    def create_a_talk_align(self, image_url, audio_url=None, top_left=[0, 0], size=0):
        """
        创建一个说话
        :return:
        """
        url = "https://api.d-id.com/talks"
        payload = {
            "script": {
                "type": "audio",
                "subtitles": "false",
                "provider": {
                    "type": "microsoft",
                    "voice_id": "en-US-JennyNeural"
                },
                "audio_url": audio_url
            },
            "config": {
                "fluent": "false",
                "pad_audio": "0.0",
                "align_driver": False,
                "stitch": True
            },
            "face": {
                "top_left": top_left,
                "size": size
            },
            "source_url": image_url
        }
        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "authorization": self.authorization
        }

        retry_delay = 5
        try_times = 3
        index = 0
        while True:
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            if response.status_code == 201:
                task_id = json.loads(response.text)['id']
                return task_id
            else:
                index = index + 1
                if index > try_times:
                    raise Exception(f"create a talk err: the err code is {response.status_code}")
                time.sleep(retry_delay)

    def get_talks(self, task_id: str):
        """
        获取一个talks
        :return:
        """
        url = f"https://api.d-id.com/talks/{task_id}"

        time.sleep(10)                                      # 冷却一段时间，给d-id生成
        retry_delay = 10
        try_times = 5
        index = 0
        while True:
            headers = {
                "accept": "application/json",
                "authorization": self.authorization
            }
            response = requests.get(url, headers=headers, timeout=30)
            info = json.loads(response.text)
            if response.status_code == 200 and "result_url" in info.keys():
                download_url = info['result_url']
                return download_url
            else:
                index = index + 1
                if index > try_times:
                    raise Exception(f"get talk err: the err code is {response.status_code}, the task_id is {task_id}")
                time.sleep(retry_delay)


if __name__ == '__main__':
    d = DiDClient("Basic YjNCbGJtRnBRR1J5WldGdFpTNWpiMjA6QUlZRU1mUHlQQTdMR1RVZ3N4RXNLOg==")
    download = d.get_talks("tlk_ivTeEEBl3kOfvBwATqu4i")
    print(download)
