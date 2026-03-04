def soma(val1, val2):
    resultado = val1 + val2
    print (resultado)

def subt(val1, val2):
    resultado = val1 - val2
    print (resultado)

def mult(val1, val2):
    resultado = val1 * val2
    print (resultado)
    
def div(val1, val2):
    if val2 == 0:
        print ('vc tá se achando engraçadinho, pondo 0 no denominador')

def bsk(a, b, c):
    import math

    d = delta(a, b, c)

    print("Seu delta é igual a:", d)

    if d < 0:
        print("Essa equação não tem raízes reais.")
    elif d == 0:
        r = -val_b / (2 * a)
        print("A equação tem apenas uma raiz real (raiz dupla):", r)
    else:
        result1 = x1(a, b, d)
        result2 = x2(a, b, d)
        print("Acabou as continhas! Viu só, você nem cansou 😉")
        print("x1 =", result1, " | x2 =", result2)

def delta(a, b, c):
    return b**2 - 4*a*c

def x1(a, b, d):
    return (-b - math.sqrt(d)) / (2 * a)

def x2(a, b, d):
    return (-b + math.sqrt(d)) / (2 * a)

# Entrada de dados

    


while 1:

    print ('bem vindo a calculadora homem macaco')
    num1 = input('digite o primeiro valor: ')
    num2 = input('digite o segundo valor: ')

    num1 = int(num1)
    num2 = int(num2)

    print ('as operações disponiveis são: soma, subtraçao, multiplicaçao, divisao e baskara')
    
    operacao = input('qual operação vc quer realizar? ')

    if (operacao == 'soma'):
        soma(num1, num2)
    
    if (operacao == 'subtraçao'):
        subt(num1, num2)

    if (operacao == 'multiplicaçao'):
        mult(num1, num2)
    
    if (operacao == 'divisao'):
        div(num1, num2)

    if (operacao == 'baskara'):
        a = input('digite o valor de a: ')
        b = input('digite o valor de b: ')
        c = input('digite o valor de c: ')
        bsk(a, b, c)

    pergunta1 = input ('quer utilizar os servisos do homem macaco de novo? ')
    
    if pergunta1 == ('nao'):
        break
