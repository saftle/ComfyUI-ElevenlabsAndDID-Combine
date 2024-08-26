#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2024/3/14 下午5:45
# @Author  : Aliang

import numpy as np
import librosa
import soundfile


def add_zero_audio(audio_path, add_time):
    y, sr = librosa.load(audio_path)
    num = add_time * sr
    zero_dst = np.zeros(num)
    y = np.hstack((y, zero_dst))
    y = np.hstack((zero_dst, y))
    soundfile.write(audio_path, y, samplerate=int(sr))


def merge_audio(audio1, audio2, audio):
    y1, sr1 = librosa.load(audio1)
    y2, sr2 = librosa.load(audio2)
    num = 0.5 * sr1
    zero_dst = np.zeros(int(num))
    y1 = np.hstack((y1, zero_dst))
    y = np.concatenate((y1, y2), axis=0)
    soundfile.write(audio, y, samplerate=int(sr1))
