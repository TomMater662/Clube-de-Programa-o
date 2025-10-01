def menu():
    def triangulo ():
        base =int(input('digite o valor da base: '))
        altura =int(input('digite o valor da altura: '))
        resultado = base * altura / 2
        return resultado
        
    def quadrado ():
        lado =int(input('digite o valor da lado: '))
        resultado = pow(lado, 2)
        return resultado
    
    def retangulo ():
        base =int(input('digite o valor da base: '))
        altura =int(input('digite o valor da altura: '))
        resultado = base * altura
        return resultado
     
    def trapézio ():
        base_menor =int(input('digite o valor da base_menor: '))
        base_maior =int(input('digite o valor da base_maior: '))
        altura =int(input('digite o valor da altura: '))
        resultado = (base_menor + base_maior) / altura * 2
        return resultado 
        
    def circulo ():
        raio =int(input('digite o valor da base: '))
        pi = 3.14
        resultado = 2 * pi * raio
        return resultado
    
    escolha1 = input(''' Cauculador de Área 3000
    T - triângulo
    Q - quadraddo
    R - retângulo
    Tr - trapézio
    C - circulo
    
    Escolha um para calcular: 
    ''')
    
    if escolha1 == 'T':
        area = triangulo()
        
    if escolha1 == 'Q':
        area = quadrado()
        
    if escolha1 == 'R':
        area = ratangulo()
        
    if escolha1 == 'Tr':
        area = trapézio()
        
    if escolha1 == 'C':
        area = circulo()
    
    
    print (f'A área é {area}')
    
    escolha2 = input('quer calcular outra área? (s/n)')
    if escolha2 == 's' : menu()
    
menu()

