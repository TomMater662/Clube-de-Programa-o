

import random

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
    
elif (player == comput) : print('empate')
else : print ('paraboins vc ganhou!!!')
   
