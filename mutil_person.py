#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2024/6/4 上午11:45
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


def videos_maker(args):
    config = read_config(args.config_path)
    did_c = DiDClient(config['did'])
    el_c = ElevenLabsClient(config['elevenlabs'])

    print("上传图片")
    image_url = did_c.upload_image("./data/no17/pic/17-18.png")
    print("上传声音文件")
    audio_url = did_c.upload_audio_file("./data/no17/audios/17-18.mp3")
    print("创建说话")
    task_id = did_c.create_a_talk_align(image_url, audio_url, top_left=[189, 48], size=422)
    print("获取说话")
    did_download_url = did_c.get_talks(task_id)
    download_from_url(did_download_url, "17-18.mp4", "./data/no17/videos")


def main(args):
    videos_maker(args)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--config_path", type=str, default="./config/config.yml", help="账号token")
    parser.add_argument("--data_path", type=str, default="./data/no12", help="数据路径")
    parser.add_argument("--sep", type=str, default=",", help="csv分隔符")
    args = parser.parse_args()
    main(args)