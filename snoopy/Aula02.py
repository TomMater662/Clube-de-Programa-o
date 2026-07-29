n = int(input('Digite a quantitade de numeros a ser falados: '))

x = []

i = 0


while 1:
    if n >= 1 and n <= 100000:
        break

    else:
        print('Valor invalido! Digite o número entre 1 e 100000')

while 1:

    if i == n:
        break
    
    digito = int(input('Digite o numero: '))

    if digito == 0:
        x.pop()
    elif digito > 0:
        x.append(digito)

    i = i + 1
resultado == sum(x)

