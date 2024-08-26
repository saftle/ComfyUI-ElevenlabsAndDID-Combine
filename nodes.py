#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2024/6/11 下午3:55
# @Author  : Aliang


import os
import folder_paths
comfy_path = os.path.dirname(folder_paths.__file__)
diffusers_path = folder_paths.get_folder_paths("diffusers")[0]

import sys
sys.path.insert(0, f'{comfy_path}/custom_nodes/comfyui-talking-head')

import pandas as pd
from .talking_head.api.did_api import DiDClient
from .talking_head.api.elevenlabs import ElevenLabsClient
from .talking_head.utils.common import read_config, deal_with_csv
from .talking_head.utils.common import download_from_url
from .talking_head.utils.common import detect_file_encoding
from audiostretchy.stretch import stretch_audio
from .talking_head.utils.audio_util import add_zero_audio
from .talking_head.utils.common import is_windows_path
from .talking_head.utils.common import validate_path
import time


#单步生成结果并返回audio和video路径
class SingleTalkingHeadRun:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "csv_path": ("STRING", {"default": ""}),
                "csv_row": ("INT", {"default": 0, "min": 0, "max": 100, "step": 1}),
            },
            "optional": {
                "image_path": ("STRING",{"default": ""}),
            },
        }

    RETURN_TYPES = ("STRING","STRING")
    RETURN_NAMES = ("audio_path","video_Path")
    FUNCTION = "TalkingHeadRun"
    CATEGORY = "TalkingHead"
    OUTPUT_NODE = True

    def TalkingHeadRun(self,**kwargs):
        if kwargs['csv_path'] is None or validate_path(kwargs['csv_path']) != True:
            raise Exception("csv is not a valid path: " + kwargs['csv_path'])
        csv_path = kwargs['csv_path']
        print(csv_path)

        #处理csv数据/创建did-elevenlabs对象
        log = ""
        config = read_config(os.path.dirname(os.path.realpath(__file__)) + "/config/config.yml")
        comfyui_path = config['comfyui_path']
        did_c = DiDClient(config['did'])
        el_c = ElevenLabsClient(config['elevenlabs'])

        #检测csv文件编码格式
        encoding = detect_file_encoding(kwargs['csv_path'])

        task_csv = pd.read_csv(csv_path, encoding=encoding)
        task_csv = deal_with_csv(task_csv, csv_path, is_trans=False)
        task_csv.to_csv(csv_path, index=False)

        # 创建各文件输出文件夹
        audio_path = f"{comfyui_path}/audios"
        if not os.path.isdir(audio_path):
            os.makedirs(audio_path)
        video_path = f"{comfyui_path}/videos"
        if not os.path.isdir(video_path):
            os.makedirs(video_path)

        shot_previous = {}
        # 制作流程
        row = task_csv.iloc[kwargs['csv_row']]
        shot_name = str(row['shot'])
        pre_shot = str(row["pre_shot"])
        print("shot_name:", shot_name, "s_text:", row['speaking_text'])
        audio_save_path = os.path.join(audio_path, shot_name + ".mp3")
        video_save_path = os.path.join(video_path, shot_name + ".mp4")
        if (str(row['speaking_text'])) == "nan":
            print("这行没有speaking_text值")
        else:
            if os.path.isfile(audio_save_path):
                print(f"the file {shot_name}.mp3 is exist")
            else:
                if pre_shot != "nan":
                    if "," in pre_shot:
                        pre_shot = pre_shot.split(",")
                    else:
                        pre_shot = [pre_shot]
                    previous_request_ids = [shot_previous.get(i, None) for i in pre_shot]
                    previous_request_ids = [i for i in previous_request_ids if i is not None]
                    request_id = el_c.generate(text=row['speaking_text'], voice=row['voice'],
                                               audio_save_path=audio_save_path,
                                               previous_request_ids=previous_request_ids)
                else:
                    request_id = el_c.generate(text=row['speaking_text'], voice=row['voice'],
                                               audio_save_path=audio_save_path, )
                shot_previous[shot_name] = request_id

        if os.path.isfile(video_save_path):
            log = log + "\t" + f"the file {shot_name}.mp4 is exist" + "\n"
            print(log)
        else:
            # if (row["mask"]) == "1":
            try:
                if kwargs['image_path']:
                    image_url = did_c.upload_image(kwargs['image_path'])
                    audio_url = did_c.upload_audio_file(audio_save_path)
                else:
                    image_url = did_c.upload_image(row['pic_path'])
                    audio_url = did_c.upload_audio_file(audio_save_path)
                if isinstance(row["align"], str):
                    x, y, s = row["align"].split(",")
                    task_id = did_c.create_a_talk_align(image_url, audio_url, top_left=[int(x), int(y)],size=int(s))
                else:
                    task_id = did_c.create_a_talk(image_url, audio_url)
                did_download_url = did_c.get_talks(task_id)
                download_from_url(did_download_url, shot_name + ".mp4", video_path)
                log = log + "\t" + f"{shot_name}.mp4 done!!!" + "\n"
            except Exception as e:
                log = log + "\t" + str(e) + "\n"
        return (audio_path,video_path)

class BatchTalkingHeadRun:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "data_path": ("STRING", {"default": ""}),
                "sep": ("STRING", {"default": ","}),
            },
        }

    RETURN_TYPES = ("STRING",)
    FUNCTION = "run"
    CATEGORY = "TalkingHead"
    OUTPUT_NODE = True

    def run(self, data_path, sep):
        data_path = os.path.join(comfy_path, f"input/{data_path}")
        print(data_path)
        if not os.path.exists(data_path):
            raise f"The folder does not exist: {data_path}"
        log = ""
        config = read_config(os.path.dirname(os.path.realpath(__file__)) + "/config/config.yml")
        did_c = DiDClient(config['did'])
        el_c = ElevenLabsClient(config['elevenlabs'])
        # 读取制作信息
        csv_path = os.path.join(data_path, "task.csv")
        task_csv = pd.read_csv(csv_path, sep=sep)
        task_csv = deal_with_csv(task_csv, data_path, is_trans=False)
        task_csv.to_csv(csv_path, index=False, sep=sep)

        # 创建各文件输出文件夹
        audio_path = data_path + "/audios"
        if not os.path.isdir(audio_path):
            os.makedirs(audio_path)

        video_path = data_path + "/videos"
        if not os.path.isdir(video_path):
            os.makedirs(video_path)

        shot_previous = {}
        # 制作流程
        for index, row in task_csv.iterrows():
            shot_name = str(row['shot'])
            pre_shot = str(row["pre_shot"])
            print("shot_name:", shot_name, "s_text:", row['speaking_text'])
            if (str(row['speaking_text'])) == "nan":
                continue

            audio_save_path = os.path.join(audio_path, shot_name + ".mp3")

            video_save_path = os.path.join(video_path, shot_name + ".mp4")
            if os.path.isfile(audio_save_path):
                print(f"the file {shot_name}.mp3 is exist")
            else:
                if pre_shot != "nan":
                    if "," in pre_shot:
                        pre_shot = pre_shot.split(",")
                    else:
                        pre_shot = [pre_shot]
                    previous_request_ids = [shot_previous.get(i, None) for i in pre_shot]
                    previous_request_ids = [i for i in previous_request_ids if i is not None]
                    request_id = el_c.generate(text=row['speaking_text'], voice=row['voice'],
                                               audio_save_path=audio_save_path,
                                               previous_request_ids=previous_request_ids)
                else:
                    request_id = el_c.generate(text=row['speaking_text'], voice=row['voice'],
                                               audio_save_path=audio_save_path, )
                shot_previous[shot_name] = request_id
                # 调整声音语速
                stretch_audio(audio_save_path, audio_save_path, ratio=1.2)
                # 增加空白语音
                add_zero_audio(audio_save_path, add_time=2)
                log = log + "\t" + f"{shot_name}.mp3 done!!!" + "\n"

            if os.path.isfile(video_save_path):
                log = log + "\t" + f"the file {shot_name}.mp4 is exist" + "\n"
            else:
                if row["mask"] == 1:
                    try:
                        image_url = did_c.upload_image(row['pic_path'])
                        audio_url = did_c.upload_audio_file(audio_save_path)
                        if isinstance(row["align"], str):
                            x, y, s = row["align"].split(",")
                            task_id = did_c.create_a_talk_align(image_url, audio_url, top_left=[int(x), int(y)],
                                                                size=int(s))
                        else:
                            task_id = did_c.create_a_talk(image_url, audio_url)
                        did_download_url = did_c.get_talks(task_id)
                        download_from_url(did_download_url, shot_name + ".mp4", video_path)
                        log = log + "\t" + f"{shot_name}.mp4 done!!!" + "\n"
                    except Exception as e:
                        log = log + "\t" + str(e) + "\n"

        return (log,)

    def IS_CHANGED(s, data_path, sep):
        return time.time()


NODE_CLASS_MAPPINGS = {
    "BatchTalkingHeadRun": BatchTalkingHeadRun,
    "🚀SingleTalkingHeadRun":SingleTalkingHeadRun,
}