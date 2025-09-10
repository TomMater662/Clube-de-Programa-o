
import random

opcoes = ['cara','coroa']

sorteio = random.randint(0,1)

escolha = input('Escolha cara ou coroa: ').lower()

if escolha == opcoes[sorteio]:
    print('Você ganhou!')
    input('Pressione Enter para sair...')
else:
    print('Você perdeu!')
    input('Pressione Enter para sair...')
