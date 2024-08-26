#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2024/5/28 下午4:19
# @Author  : Aliang


from audiostretchy.stretch import stretch_audio
from talking_head.utils.audio_util import add_zero_audio


def main(save_file):
    # 调整声音语速
    stretch_audio(save_file, save_file, ratio=1.3)
    # 增加空白语音
    add_zero_audio(save_file, add_time=2)


if __name__ == '__main__':
    save_file = "8-27.mp3"
    main(save_file)