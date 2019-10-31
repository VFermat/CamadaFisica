
import numpy as np
import sounddevice as sd
import matplotlib.pyplot as plt
from scipy.fftpack import fft
from scipy import signal as window


class signalMeu:
    def __init__(self):
        self.init = 0

    def generateSin(self, frequency, amplitude, time, sampleRate):
        # Número de pontos que teremos.
        n = time * sampleRate

        # Lista com todos os pontos do eixo X.
        x = np.linspace(0.0, time, n)

        # Lista com todos os pontos do eixo Y.
        y = amplitude * np.sin(2 * np.pi * frequency * x)

        return (x, y)

    def calcFFT(self, signal, fs):
        # https://docs.scipy.org/doc/scipy/reference/tutorial/fftpack.html
        N = len(signal)
        W = window.hamming(N)
        T = 1/fs
        xf = np.linspace(0.0, 1.0/(2.0*T), N//2)
        yf = fft(signal*W)
        return(xf, np.abs(yf[0:N//2]))

    def plotFFT(self, signal, fs):
        x, y = self.calcFFT(signal, fs)
        plt.figure()
        plt.plot(x, np.abs(y))
        plt.title('Fourier')
        plt.show()
