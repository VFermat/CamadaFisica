from scipy.signal import butter, lfilter, freqz
from suaBibSignal import signalMeu
import matplotlib.pyplot as plt
from scipy.io import wavfile
from scipy import signal
import sounddevice as sd
import numpy as np
import time


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

    # Tempo de duração da gravação.
    duration = 10

    # Taxa de amostragem.
    fs = 44100

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
    audio = sd.rec(int(duration * fs), channels=channels)
    sd.wait()

    # Pegando o vetor correto.
    audio = [a[0] for a in audio]
    audio = np.array(audio)

    # Calculando FFT.
    xf, yf = bib.calcFFT(audio, fs)

    # Plotando o gráfico do FFT.
    plt.title("Fourier Audio")
    plt.figure("F(y) AM recebido")
    plt.plot(xf, yf)
    plt.grid()

    # Criando o eixo X do áudio, usado para plotar os gráficos.
    time = np.linspace(0.0, duration, len(audio))

    # Plotando o áudio.
    plt.figure()
    plt.title("AM recebido")
    plt.plot(time[:400], audio[:400])

    # Criando a onda portadora.
    _, carrier = bib.generateSin(14000, 1, duration, fs)

    # Multiplicando a onde recebida pela portadora.
    multiplication = audio * carrier

    # Filtro passa baixa.
    output = butter_lowpass_filter(multiplication, 4000, fs, 10)

    # Calculando FFT.
    xf, yf = bib.calcFFT(output, fs)

    # Plotando o gráfico do FFT.
    plt.title("Fourier Audio")
    plt.figure("F(y) demodulado")
    plt.plot(xf, yf)
    plt.grid()

    # Plotando o áudio.
    plt.figure()
    plt.title("AM demodulado")
    plt.plot(time, output)

    # Dando play na onda de saída.
    sd.play(output, fs)
    sd.wait()
    plt.show()
