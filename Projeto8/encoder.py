from suaBibSignal import signalMeu
import matplotlib.pyplot as plt
from scipy.io import wavfile
from scipy import signal
import sounddevice as sd
import numpy as np


if __name__ == "__main__":
    # Criando o objeto da biblioteca fornecida.
    bib = signalMeu()

    # Lendo o arquivo de áudio(.wav).
    fs, data = wavfile.read("./Leeroy_Jenkins.wav")

    # Duração do áudio.
    duration = len(data) / fs

    # Criando o eixo X do áudio, usado para plotar os gráficos.
    time = np.linspace(0.0, duration, len(data))

    # Plotando o áudio original.
    plt.figure()
    plt.title("Áudio Original")
    plt.plot(time, data)

    # Normalização para número de 16-bit.
    normalized = [x/32768 for x in data]

    # Plotando o áudio normalizado.
    plt.figure()
    plt.title("Áudio Normalizado")
    plt.plot(time, normalized)

    # Filtro passa baixa.
    nyq_rate = fs/2
    width = 5.0/nyq_rate
    ripple_db = 60.0
    N, beta = signal.kaiserord(ripple_db, width)
    cutoff_hz = 4000.0
    taps = signal.firwin(N, cutoff_hz/nyq_rate, window=('kaiser', beta))
    normalizedLPF = signal.lfilter(taps, 1.0, normalized)

    # Criando a onde portadora.
    x, carrier = bib.generateSin(14000, 1, duration, fs)

    # Gerando a onde a ser enviada.
    output = [normalizedLPF[i] * carrier[i] for i in range(len(carrier))]

    # Plotando a onda de saída.
    plt.figure()
    plt.title("Output Wave")
    plt.plot(time, output)

    # Dando play na onda de saída.
    sd.play(output, fs)
    sd.wait()

    # Mostrando todos os gráficos.
    plt.show()
