nun7 = int(input('Digite a primeira nota '))
nun8 = int(input('Digite a segunda nota '))
nun9 = int(input('Digite a terceira nota '))
nun10 = int(input('Digite a quarta nota '))
resultado = 0

resultado = (nun7 + nun9 + nun8 + nun10) / 4 
print('a média é ' +str(resultado))


if (resultado<=10) and (resultado>=6):
    print ('Aprovado')
    
elif (resultado<5) (resultado>=0):
    print ('Reprovado')
    
elif (resultado<6) and (resultado>=5):
    print ('Recuperação')

else :
    print ('Recuperação')
