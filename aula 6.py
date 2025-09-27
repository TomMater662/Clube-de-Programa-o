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
    
    else:
        (resultado == val1 + val2)
        print (resultado)

while 1:
    print ('bem vindo a calculadora homem macaco')
    num1 = input('digite o primeiro valor: ')
    num2 = input('digite o segundo valor: ')

    num1 = int(num1)
    num2 = int(num2)

    print ('as operações disponiveis são: soma, subtraçao, multiplicaçao e divisao')
    
    operacao = input('qual operação vc quer realizar? ')

    if (operacao == 'soma'):
        soma(num1, num2)
    
    if (operacao == 'subtraçao'):
        subt(num1, num2)

    if (operacao == 'multiplicaçao'):
        mult(num1, num2)
    
    if (operacao == 'divisao'):
        div(num1, num2)

    pergunta1 = input ('quer utilizar os servisos do homem macaco de novo? ')
    
    if pergunta1 == ('nao'):
        break
