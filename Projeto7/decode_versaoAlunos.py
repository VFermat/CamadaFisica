from suaBibSignal import signalMeu
import matplotlib.pyplot as plt
import sounddevice as sd
import peakutils
import numpy as np
import sys
import time


dfmtTable = [
    ["1", 697, 1209],
    ["2", 697, 1336],
    ["3", 697, 1477],
    ["A", 697, 1673],
    ["4", 770, 1209],
    ["5", 770, 1336],
    ["6", 770, 1477],
    ["B", 770, 1673],
    ["7", 852, 1209],
    ["8", 852, 1336],
    ["9", 852, 1477],
    ["C", 852, 1673],
    ["X", 941, 1209],
    ["0", 941, 1336],
    ["#", 941, 1477],
    ["D", 941, 1673]
]


def todB(s):
    """
    Converte intensidade para dB.
    """
    sdB = 10*np.log10(s)
    return(sdB)


def main():
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
    print("Recording...")

    # Gravando o áudio.
    audio = sd.rec(int(duration * sampleRate), channels=channels)
    sd.wait()

    # 
    audio2 = [a[0] for a in audio]

    # Calculando FFT.
    xf, yf = bib.calcFFT(audio2, sampleRate)
    
    # Plotando o gráfico do FFT.
    plt.title("Fourier Audio")
    plt.figure("F(y)")
    plt.plot(xf, yf)
    plt.grid()
    plt.show()

    # Pegando o índice de cada pico (onde está na lista).
    indexes = peakutils.indexes(yf, 0.05, min_dist=100)

    # Pegando os picos de acorco com os índices encontrados.
    # Ignoramos os índices que não estão entre 600Hz e 2000Hz.
    peaks = [xf[i] for i in indexes if xf[i] > 600 and xf[i] < 2000]

    # Printando os picos.
    print(f"Peaks: {peaks}")

    # Verificando se os picos estão dentro da tabela de números, incluindo a margem de erro.
    margin = 10
    for entry in dfmtTable:
        number = entry[0]

        first = False
        second = False

        for peak in peaks:
            if (entry[1] - margin <= peak <= entry[1] + margin): 
                first = True

            if (entry[2] - margin <= peak <= entry[2] + margin):
                second = True

        if (first and second):
            print(f"Number is: {number}")

        # if (entry[1] - margin <= peaks[0] <= entry[1] + margin and entry[2] - margin <= peaks[1] <= entry[2] + margin):
        #     print(f"Number is: {number}")


if __name__ == "__main__":
    main()
