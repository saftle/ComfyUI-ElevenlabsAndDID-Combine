#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2024/3/14 下午8:08
# @Author  : Aliang

import os
import uuid
import re
from elevenlabs.base_client import BaseElevenLabs
from elevenlabs.environment import ElevenLabsEnvironment
import typing
import httpx
from typing import Iterator, Optional, Union, \
  Optional, AsyncIterator
from elevenlabs.types import Voice
from elevenlabs.types import Voice, VoiceSettings, \
  PronunciationDictionaryVersionLocator, Model
from elevenlabs.core import RequestOptions, ApiError
from elevenlabs import save
from .text_to_speech_client import TextToSpeechClient


DEFAULT_VOICE = Voice(
    voice_id="EXAVITQu4vr4xnSDxMaL",
    name="Rachel",
    settings=VoiceSettings(
        stability=0.71, similarity_boost=0.5, style=0.0, use_speaker_boost=True
    ),
)

VoiceId = str
VoiceName = str
ModelId = str

OMIT = typing.cast(typing.Any, ...)
def is_voice_id(val: str) -> bool:
    return bool(re.match(r"^[a-zA-Z0-9]{20}$", val))


class ElevenLabs(BaseElevenLabs):
    def __init__(
        self,
        *,
        base_url: typing.Optional[str] = None,
        environment: ElevenLabsEnvironment = ElevenLabsEnvironment.PRODUCTION,
        api_key: typing.Optional[str] = os.getenv("ELEVEN_API_KEY"),
        timeout: typing.Optional[float] = 60,
        httpx_client: typing.Optional[httpx.Client] = None
    ):
        super().__init__(
            base_url=base_url,
            environment=environment,
            api_key=api_key,
            timeout=timeout,
            httpx_client=httpx_client
        )
        self.api_key = api_key
        self.text_to_speech = TextToSpeechClient(client_wrapper=self._client_wrapper)

    def generate(
            self,
            *,
            text: Union[str, Iterator[str]],
            voice: Union[VoiceId, VoiceName, Voice] = DEFAULT_VOICE,
            voice_settings: typing.Optional[VoiceSettings] = DEFAULT_VOICE.settings,
            model: Union[ModelId, Model] = "eleven_monolingual_v1",
            optimize_streaming_latency: typing.Optional[int] = 0,
            stream: bool = False,
            output_format: Optional[str] = "mp3_44100_128",
            pronunciation_dictionary_locators: typing.Optional[
                typing.Sequence[PronunciationDictionaryVersionLocator]
            ] = OMIT,
            request_options: typing.Optional[RequestOptions] = None,
            previous_request_ids: typing.Optional[RequestOptions] = None
    ):
        """
            - text: Union[str, Iterator[str]]. The string or stream of strings that will get converted into speech.

            - voice: str. A voice id, name, or voice response. Defaults to the Rachel voice.

            - model: typing.Optional[str]. Identifier of the model that will be used, you can query them using GET /v1/models.
                                           The model needs to have support for text to speech, you can check this using the
                                           can_do_text_to_speech property.

            - optimize_streaming_latency: typing.Optional[int]. You can turn on latency optimizations at some cost of quality. The best possible final latency varies by model. Possible values:
                                                                0 - default mode (no latency optimizations)
                                                                1 - normal latency optimizations (about 50% of possible latency improvement of option 3)
                                                                2 - strong latency optimizations (about 75% of possible latency improvement of option 3)
                                                                3 - max latency optimizations
                                                                4 - max latency optimizations, but also with text normalizer turned off for even more latency savings (best latency, but can mispronounce eg numbers and dates).

                                                                Defaults to 0.

            - stream: bool. If true, the function will return a generator that will yield the audio in chunks.

                            Defaults to False.

            - output_format: typing.Optional[str]. Output format of the generated audio. Must be one of:
                                                   mp3_22050_32 - output format, mp3 with 22.05kHz sample rate at 32kbps.
                                                   mp3_44100_32 - output format, mp3 with 44.1kHz sample rate at 32kbps.
                                                   mp3_44100_64 - output format, mp3 with 44.1kHz sample rate at 64kbps.
                                                   mp3_44100_96 - output format, mp3 with 44.1kHz sample rate at 96kbps.
                                                   mp3_44100_128 - default output format, mp3 with 44.1kHz sample rate at 128kbps.
                                                   mp3_44100_192 - output format, mp3 with 44.1kHz sample rate at 192kbps. Requires you to be subscribed to Creator tier or above.
                                                   pcm_16000 - PCM format (S16LE) with 16kHz sample rate.
                                                   pcm_22050 - PCM format (S16LE) with 22.05kHz sample rate.
                                                   pcm_24000 - PCM format (S16LE) with 24kHz sample rate.
                                                   pcm_44100 - PCM format (S16LE) with 44.1kHz sample rate. Requires you to be subscribed to Independent Publisher tier or above.
                                                   ulaw_8000 - μ-law format (sometimes written mu-law, often approximated as u-law) with 8kHz sample rate. Note that this format is commonly used for Twilio audio inputs.

                                                    Defaults to mp3_44100_128.

            - voice_settings: typing.Optional[VoiceSettings]. Voice settings overriding stored setttings for the given voice. They are applied only on the given request.

            - pronunciation_dictionary_locators: typing.Optional[typing.Sequence[PronunciationDictionaryVersionLocator]]. A list of pronunciation dictionary locators (id, version_id) to be applied to the text. They will be applied in order. You may have up to 3 locators per request

            - request_options: typing.Optional[RequestOptions]. Request-specific configuration.
        """
        if isinstance(voice, str) and is_voice_id(voice):
            voice_id = voice
        elif isinstance(voice, str):
            voices_response = self.voices.get_all(request_options=request_options)
            maybe_voice_id = next((v.voice_id for v in voices_response.voices if v.name == voice), None)
            if maybe_voice_id is None:
                raise ApiError(body=f"Voice {voice} not found.")
            voice_id = maybe_voice_id
        elif isinstance(voice, Voice):
            voice_id = voice.voice_id
            if voice_settings == DEFAULT_VOICE.settings \
                    and voice.settings is not None:
                voice_settings = voice.settings
        else:
            voice_id = DEFAULT_VOICE.voice_id

        if isinstance(model, str):
            model_id = model
        elif isinstance(model, Model):
            model_id = model.model_id
        else:
            raise ApiError(body="Model is neither a string nor a model.")

        if stream:
            if isinstance(text, str):
                return self.text_to_speech.convert_as_stream(
                    voice_id=voice_id,
                    voice_settings=voice_settings,
                    optimize_streaming_latency=optimize_streaming_latency,
                    output_format=output_format,
                    text=text,
                    request_options=request_options,
                    pronunciation_dictionary_locators=pronunciation_dictionary_locators,
                    model_id=model_id
                )
            elif isinstance(text, Iterator):
                return self.text_to_speech.convert_realtime(  # type: ignore
                    voice_id=voice_id,
                    voice_settings=voice_settings,
                    text=text,
                    request_options=request_options,
                    model_id=model_id
                )
            else:
                raise ApiError(body="Text is neither a string nor an iterator.")
        else:
            if not isinstance(text, str):
                raise ApiError(body="Text must be a string when stream is False.")
            return self.text_to_speech.convert(
                voice_id=voice_id,
                model_id=model_id,
                voice_settings=voice_settings,
                optimize_streaming_latency=optimize_streaming_latency,
                output_format=output_format,
                text=text,
                request_options=request_options,
                pronunciation_dictionary_locators=pronunciation_dictionary_locators,
                previous_request_ids=previous_request_ids
            )


class ElevenLabsClient(object):
    def __init__(self, api_key):
        self.client = ElevenLabs(api_key=api_key)
        self.model = "eleven_multilingual_v2"

    def generate(self, text, voice, audio_save_path, previous_request_ids=None):
        audio, request_id = self.client.generate(
            text=text,
            voice=voice,
            previous_request_ids=previous_request_ids,
            model=self.model)
        save(audio, audio_save_path)
        return request_id
