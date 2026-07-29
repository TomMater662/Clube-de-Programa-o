
import math

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

def bsk(vala, valb, valc):
    

    d = delta(vala, valb, valc)

    print("Seu delta é igual a:", d)

    if d < 0:
        print("Essa equação não tem raízes reais.")
    elif d == 0:
        r = -b / (2 * a)
        print("A equação tem apenas uma raiz real (raiz dupla):", r)
    else:
        result1 = x1(vala, valb, d)
        result2 = x2(vala, valb, d)
        print("Acabou as continhas! Viu só, você nem cansou 😉")
        print("x1 =", result1, " | x2 =", result2)

def delta(vala, valb, valc):
    return valb**2 - 4*vala*valc

def x1(vala, valb, d):
    return (-b - math.sqrt(d)) / (2 * a)

def x2(vala, valb, d):
    return (-b + math.sqrt(d)) / (2 * a)

# Entrada de dados

    


while 1:

    print ('bem vindo a calculadora homem macaco')

    print ('as operações disponiveis são: soma, subtraçao, multiplicaçao, divisao e baskara')
    
    operacao = input('qual operação vc quer realizar? ')
    
    if (operacao == 'soma'):    
        num1 = input('digite o primeiro valor: ')
        num2 = input('digite o segundo valor: ')
        num1 = int(num1)
        num2 = int(num2)
        soma(num1, num2)
    
    if (operacao == 'subtraçao'):    
        num1 = input('digite o primeiro valor: ')
        num2 = input('digite o segundo valor: ')
        num1 = int(num1)
        num2 = int(num2)
        subt(num1, num2)

    if (operacao == 'multiplicaçao'):
        
        num1 = input('digite o primeiro valor: ')
        num2 = input('digite o segundo valor: ')
        num1 = int(num1)
        num2 = int(num2)
        mult(num1, num2)
    
    if (operacao == 'divisao'):
        num1 = input('digite o primeiro valor: ')
        num2 = input('digite o segundo valor: ')
        num1 = int(num1)
        num2 = int(num2)
        div(num1, num2)

    if (operacao == 'baskara'):
        numa = input('digite o valor de a: ')
        numb = input('digite o valor de b: ')
        numc = input('digite o valor de c: ')
        numa = int(numa)
        numb
        bsk(numa, numb, numc)

    pergunta1 = input ('quer utilizar os servisos do homem macaco de novo? ')
    
    if pergunta1 == ('nao'):
        break
