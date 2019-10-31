from suaBibSignal import signalMeu
import matplotlib.pyplot as plt
from scipy.io import wavfile
from scipy import signal
import sounddevice as sd
import numpy as np
import time


if __name__ == "__main__":
    # Criando o objeto da biblioteca fornecida.
    bib = signalMeu()

    # Tempo de duração da gravação.
    duration = 3

    # Taxa de amostragem.
    sampleRate = 44100

    # Número de canais a serem gravados.
    channels = 1

    time.sleep(1)
    print("3...")

    time.sleep(1)
    print("2...")

    time.sleep(1)
    print("1...")
    print("Gravando...")

    # Gravando o áudio.
    audio = sd.rec(int(duration * sampleRate), channels=channels)
    sd.wait()
