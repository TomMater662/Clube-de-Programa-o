import random

numero_secreto = random.randint(1, 100)
tentativas = 0
max_tentativas = 7


def fase3 ():
    print ("""Parabéns! Você Ganhou!\n
Você Passou Para 3° Fase!""")
    b = ['0', '1', '2', '3', '4', '5', '6', '7', '8']
    print (f'{b[0]} | {b[1]} | {b[2]}')
    print ('---------')
    print (f'{b[3]} | {b[4]} | {b[5]}')
    print ('---------')
    print (f'{b[6]} | {b[7]} | {b[8]}')
    while 1:
        x = int(input('Vez do "X". Qual posição você quer colocar?'))
        b[x] = ('X')
        print (f'{b[0]} | {b[1]} | {b[2]}')
        print ('---------')
        print (f'{b[3]} | {b[4]} | {b[5]}')
        print ('---------')
        print (f'{b[6]} | {b[7]} | {b[8]}')

        o  = int(input('Vez do "O". Qual posição você quer colocar?'))
        b[o] = ('O')
        print (f'{b[0]} | {b[1]} | {b[2]}')
        print ('---------')
        print (f'{b[3]} | {b[4]} | {b[5]}')
        print ('---------')
        print (f'{b[6]} | {b[7]} | {b[8]}')

        if {{b[0]}, {b[1]}, {b[2]}} == ('X') or {{b[3]}, {b[4]}, {b[5]}} == ('X') or {{b[6]}, {b[7]}, {b[8]}} == ('X') or {{b[0]}, {b[3]}, {b[6]}} == ('X') or {{b[1]}, {b[4]}, {b[7]}} == ('X') or {{b[3]}, {b[5]}, {b[8]}} == ('X') or {{b[0]}, {b[4]}, {b[8]}} == ('X') or {{b[2]}, {b[4]}, {b[6]}} == ('X'):
            print ('"X" ganhou!')
        if {{b[0]}, {b[1]}, {b[2]}} == ('O') or {{b[3]}, {b[4]}, {b[5]}} == ('O') or {{b[6]}, {b[7]}, {b[8]}} == ('O') or {{b[0]}, {b[3]}, {b[6]}} == ('O') or {{b[1]}, {b[4]}, {b[7]}} == ('O') or {{b[3]}, {b[5]}, {b[8]}} == ('O') or {{b[0]}, {b[4]}, {b[8]}} == ('O') or {{b[2]}, {b[4]}, {b[6]}} == ('O'):
            print ('"O" ganhou!')

def fase2 ():
    print ("""Parabéns! Você Ganhou!\n
Você Passou Para 2° Fase!""")
    
    import random

    while 1:
        
        alea = random.randint(0, 2)

        opcao = ['tesoura', 'papel', 'pedra']

        comput = opcao[alea]

        player = input('pedra, papel ou tesoura? ')

        if (comput == 'pedra' and player == 'tesoura'):
            print ('computador ganhou') 

        elif (comput == 'tesoura' and player == 'papel'):
            print ('computador ganhou') 

        elif (comput == 'papel' and player == 'pedra'):
            print ('computador ganhou') 
    
        elif (player == comput) : 
            print('empate')
        else : 
            print ('Paraboins você ganhou!')
            break
   

print("""Bem-vindo ao Joguinho de Bananas \n
1° Fase: Jogo de Adivinhação!""")

while tentativas < max_tentativas:
    palpite = int(input("Tente adivinhar o número de 1 a 100: "))
    tentativas += 1

    if palpite == numero_secreto:
        fase2 ()
        break
    elif palpite > numero_secreto:
        print("Tente um número menor.")
    else:
        print("Tente um número maior.")

if tentativas == max_tentativas and palpite != numero_secreto:
    print(f"Game Over. O número era {numero_secreto} Tente novamente...")


fase3 ()