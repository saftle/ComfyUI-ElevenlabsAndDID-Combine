#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2024/4/29 下午4:50
# @Author  : Aliang

import pysrt
import glob
import deepl
import os
from tqdm import tqdm


def translate(text):
    auth_key = "262a795b-f031-44a2-ac19-54a851150c3a:fx"
    translator = deepl.Translator(auth_key)
    result = translator.translate_text(text, target_lang="ZH")
    return result.text


def srt_translate():
    for filename in glob.glob("srt_data/srt/*.srt"):
        srt = pysrt.open(filename)
        srt_filename = os.path.basename(filename)
        for sentence in tqdm(srt.data):
            text = sentence.text
            translated = translate(text)
            # sentence.text = translated                    # 中文版本
            sentence.text = text + "\n" + translated        # 中英版本
        srt.save(os.path.join("srt_data/srt_t", srt_filename))


if __name__ == '__main__':
    srt_translate()