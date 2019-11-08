from scipy.signal import butter, lfilter, freqz
from suaBibSignal import signalMeu
import matplotlib.pyplot as plt
from scipy.io import wavfile
from scipy import signal
import sounddevice as sd
import numpy as np


def butter_lowpass(cutoff, fs, order=5):
    nyq = 0.5 * fs
    normal_cutoff = cutoff / nyq
    b, a = butter(order, normal_cutoff, btype='low', analog=False)
    return b, a


def butter_lowpass_filter(data, cutoff, fs, order=5):
    b, a = butter_lowpass(cutoff, fs, order=order)
    y = lfilter(b, a, data)
    return y


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
    data = np.array(data)
    div = max(abs(data))
    normalized = data/div

    # Plotando o áudio normalizado.
    plt.figure()
    plt.title("Áudio Normalizado")
    plt.plot(time, normalized)

    # Calculando FFT.
    xf, yf = bib.calcFFT(normalized, fs)

    # Plotando o gráfico do FFT.
    plt.title("Fourier Audio")
    plt.figure("F(y) Antes de modular")
    plt.plot(xf, yf)
    plt.grid()

    # Get the filter coefficients so we can check its frequency response.
    normalizedLPF = butter_lowpass_filter(normalized, 4000, fs, 10)

    # Criando a onda portadora.
    x, carrier = bib.generateSin(14000, 1, duration, fs)

    # Gerando a onda a ser enviada.
    output = normalizedLPF * carrier

    # Calculando FFT.
    xf, yf = bib.calcFFT(output, fs)

    # Plotando o gráfico do FFT.
    plt.title("Fourier Audio depois de modular")
    plt.figure("F(y)")
    plt.plot(xf, yf)
    plt.grid()

    # Plotando a onda de saída.
    plt.figure()
    plt.title("Output Wave")
    plt.plot(time, output)

    # Dando play na onda de saída.
    sd.play(output, fs)
    sd.wait()

    # Mostrando todos os gráficos.
    # plt.show()
