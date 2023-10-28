import speech_recognition as sr
import argparse
import sounddevice

from queue import Queue
from sys import platform
from time import sleep



def main():
    parser = argparse.ArgumentParser()
    if 'linux' in platform:
        parser.add_argument("--default_microphone", default='pulse',
                            help="Default microphone name for SpeechRecognition. "
                                 "Run this with 'list' to view available Microphones.", type=str)
    parser.add_argument("--record_timeout", default=30,
                        help="How real time the recording is in seconds.", type=float)
    parser.add_argument("--model", default="medium", help="Model to use",
                        choices=["tiny", "base", "small", "medium", "large",
                                 "tiny.en", "base.en", "small.en", "medium.en"])
    parser.add_argument("--language", default=None,
                            help="Language for transcription.", type=str)
    parser.add_argument("--energy_threshold", default=2000,
                        help="Energy level for mic to detect.", type=int)
    parser.add_argument("--phrase_threshold", default=0.5,
                        help="minimum seconds of speaking audio"
                             "before we consider the speaking audio a phrase.", type=float)
    parser.add_argument("--microphone_calibrate", action='store_true',
                        help="Automatic calibration for microphone level.")  
    args = parser.parse_args()    
    

    if 'linux' in platform:
        mic_name = args.default_microphone
        if not mic_name or mic_name == 'list':
            print("Available microphone devices are: ")
            for index, name in enumerate(sr.Microphone.list_microphone_names()):
                print(f"Microphone with name \"{name}\" found")
            return
        else:
            for index, name in enumerate(sr.Microphone.list_microphone_names()):
                if mic_name in name:
                    source = sr.Microphone(sample_rate=16000, device_index=index)
                    break
    else:
        source = sr.Microphone(sample_rate=16000)


    phrase_queue = Queue()
    recorder = sr.Recognizer()
    recorder.energy_threshold = args.energy_threshold
    recorder.dynamic_energy_threshold = False
    recorder.phrase_threshold = args.phrase_threshold
    if args.microphone_calibrate:
        with source:
            print("Please wait. Calibrating microphone...")
            recorder.adjust_for_ambient_noise(source, duration=1)
    
    def record_callback(_, audio:sr.AudioData) -> None:
        phrase_queue.put(audio)
        print("New phrase added. Being processed...")
    
    recorder.listen_in_background(source, record_callback, phrase_time_limit=args.record_timeout)

    while True:
        if not phrase_queue.empty():
            audio_data = phrase_queue.get()
            transcript = recorder.recognize_whisper(audio_data, args.model, language=args.language)
            print(transcript)
            sleep(0.25)


if __name__ == '__main__':
    main()