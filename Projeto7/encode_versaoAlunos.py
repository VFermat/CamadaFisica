from suaBibSignal import signalMeu
import matplotlib.pyplot as plt
import sounddevice as sd
import numpy as np
import sys


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


def signal_handler(signal, frame):
    print('You pressed Ctrl+C!')
    sys.exit(0)


def todB(s):
    """
    Converte intensidade para dB.
    """
    sdB = 10*np.log10(s)
    return(sdB)


def main():
    # Criando o objeto da biblioteca fornecida.
    bib = signalMeu()

    # Taxa de amostragem.
    sampleRate = 44100

    # Tempo de duração por caracter.
    duration = 0.5

    # Amplitude.
    amplitude = 1

    # Pegando o número do usuário.
    number = input("Number: ")

    # Declarando o sinal a ser criado.
    signal = []

    print("[LOG] Generating the sine waves.")
    # Passando por cada caracter do número.
    for char in number:
        # Passando por cada letra presente na tabela. 
        for letter in dfmtTable:
            # Verificando se são iguais.
            if char == letter[0]:

                # Gerando as senoides.
                time, wave = bib.generateSin(letter[1], amplitude, duration, sampleRate)
                time, wave2 = bib.generateSin(letter[2], amplitude, duration, sampleRate)

                # Adicionando as senoides ao final do sinal.
                signal.extend(wave + wave2)
                plt.plot(time[:400], wave[:400] + wave2[:400])

                _, noSound = bib.generateSin(10, 0, 0.1, sampleRate)
                signal.extend(noSound)

    print("[LOG] Playing the generated sound.")
    # Mostrando o áudio e esperando ele terminar.
    sd.play(signal, sampleRate)
    sd.wait()
    
    # Plotando a transformada do sinal.
    # bib.plotFFT(signal, sampleRate)
    # plt.show()


if __name__ == "__main__":
    main()
