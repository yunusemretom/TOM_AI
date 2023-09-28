import json
import time
import tkinter as tk
import webbrowser
from random import randint
import multiprocessing as mp

import wave
import pyaudio
import pyttsx3
import requests
from PIL import Image, ImageTk
from pynput.keyboard import Controller, Key
from vosk import KaldiRecognizer, Model