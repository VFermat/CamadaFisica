# Descrição do Protocolo Usado

O protocolo escolhido pela dupla se baseia na comunicação através do envio de pacotes. Cada pacote contém um HEAD, um PAYLOAD e um EOP.

A estrutura do HEAD é:
    HEAD[25] = fileSize[4] + fileName[15] + fileExtension[5] + bytesStuffed[1]

O EOP escolhido é:
    EOP = 0xD5 + 0xD6 + 0xD7 + 0xD8

É checado se o EOP aparece no pacote apenas na parte do PAYLOAD. Caso ele apareca, é substituido por:
    0xD5 + 0x00 + 0xD6 + 0x00 + 0xD7 + 0x00 + 0xD8

As resposta do servidor podem ser:
    "Success": bytes([190])
    "Size mismatch": bytes([191])
    "EOP not found": bytes([192])
    "EOP in wrong place": bytes([193])