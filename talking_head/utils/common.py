#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2024/3/18 下午2:29
# @Author  : Aliang
import logging
import re
import chardet
import yaml
import os
import pandas as pd
import deepl
import requests


def download_from_url(url, file_name, save_dir=None):
    if save_dir is None:
        save_dir = "/tmp/audio"
        if not os.path.isdir(save_dir):
            os.makedirs(save_dir)
    response = requests.get(url)
    with open(os.path.join(save_dir, file_name), "wb") as w:
        w.write(response.content)


def read_config(config_path):
    with open(config_path, 'rb') as f:
        config = yaml.safe_load(f)
    return config


def deal_with_csv(data: pd.DataFrame, data_path, is_trans=False):
    def get_translator(x):
        return x.text
    auth_key = "1b0c91c8-5354-d3e6-6d31-51e2955be432:fx"
    translator = deepl.Translator(auth_key)
    data_path = data_path + "/pic"
    if "pic_name" in data.keys():
        data['pic_path'] = data["pic_name"].apply(lambda x: os.path.join(data_path, x))
    else:
        data['pic_path'] = data['shot'].apply(lambda x: os.path.join(data_path, str(x) + ".png"))
    if is_trans:
        data['trans_text'] = data['speaking_text'].apply(lambda x: get_translator(translator.translate_text(x, target_lang="EN-US")))
    else:
        data['trans_text'] = data['speaking_text']
    return data

def is_windows_path(path):
    return bool(re.match(r'^[a-zA-Z]:\\', path))

def validate_path(path, allow_none=False, allow_url=True):
    if path is None:
        return allow_none
    if is_windows_path(path):
        if not allow_url:
            return "URLs are unsupported for this path"
        return is_safe_path(path)
    if not os.path.isfile(strip_path(path)):
        return "Invalid file path: {}".format(path)
    return is_safe_path(path)

def is_safe_path(path):
        return True

def strip_path(path):
    path = path.strip()
    logging.log(logging.INFO,path)
    if path.startswith("\""):
        path = path[1:]
    if path.endswith("\""):
        path = path[:-1]
    return path

def detect_file_encoding(file_path):
    with open(file_path, 'rb') as f:
        result = chardet.detect(f.read())
    return result['encoding']