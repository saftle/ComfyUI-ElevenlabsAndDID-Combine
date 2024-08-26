#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2024/3/14 下午1:54
# @Author  : Aliang

import os
import argparse
import pandas as pd
from talking_head.api.did_api import DiDClient
from talking_head.api.elevenlabs import ElevenLabsClient
from talking_head.utils.common import read_config, deal_with_csv
from talking_head.utils.common import download_from_url
from audiostretchy.stretch import stretch_audio
from talking_head.utils.audio_util import add_zero_audio


def maker(args):
    config = read_config(args.config_path)
    did_c = DiDClient(config['did'])
    el_c = ElevenLabsClient(config['elevenlabs'])

    # 读取制作信息
    csv_path = os.path.join(args.data_path, "task.csv")
    task_csv = pd.read_csv(csv_path, sep=args.sep)
    task_csv = deal_with_csv(task_csv, args.data_path, is_trans=False)
    task_csv.to_csv(csv_path, index=False, sep=args.sep)

    # 创建各文件输出文件夹
    audio_path = args.data_path + "/audios"
    if not os.path.isdir(audio_path):
        os.makedirs(audio_path)

    video_path = args.data_path + "/videos"
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

        audio_save_path = os.path.join(audio_path, shot_name+".mp3")

        video_save_path = os.path.join(video_path, shot_name+".mp4")
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
                                           audio_save_path=audio_save_path,)
            shot_previous[shot_name] = request_id
            # 调整声音语速
            stretch_audio(audio_save_path, audio_save_path, ratio=1.2)
            # 增加空白语音
            add_zero_audio(audio_save_path, add_time=2)

        if os.path.isfile(video_save_path):
            print(f"the file {shot_name}.mp4 is exist")
        else:
            if row["mask"] == 1:
                try:
                    print("上传图片")
                    image_url = did_c.upload_image(row['pic_path'])
                    print("上传声音文件")
                    audio_url = did_c.upload_audio_file(audio_save_path)
                    print("创建说话")
                    if isinstance(row["align"], str):
                        x, y, s = row["align"].split(",")
                        task_id = did_c.create_a_talk_align(image_url, audio_url, top_left=[int(x), int(y)], size=int(s))
                    else:
                        task_id = did_c.create_a_talk(image_url, audio_url)
                    print("获取说话")
                    did_download_url = did_c.get_talks(task_id)
                    download_from_url(did_download_url, shot_name+".mp4", video_path)
                except Exception as e:
                    print(e)


def main(args):
    maker(args)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--config_path", type=str, default="./config/config.yml", help="账号token")
    parser.add_argument("--data_path", type=str, default="./data/黑手党第二集", help="数据路径")
    parser.add_argument("--sep", type=str, default=",", help="csv分隔符")
    args = parser.parse_args()
    for i in range(3):
        main(args)
