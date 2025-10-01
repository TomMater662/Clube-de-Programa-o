import math

print("Bem-vindo ao anti-para-casa")
print("Aqui você poderá fazer fórmula de Bhaskara sem suar")

def delta(a, b, c):
    return b**2 - 4*a*c

def x1(a, b, d):
    return (-b - math.sqrt(d)) / (2 * a)

def x2(a, b, d):
    return (-b + math.sqrt(d)) / (2 * a)

# Entrada de dados
val_a = int(input("Digite o valor de a: "))
val_b = int(input("Digite o valor de b: "))
val_c = int(input("Digite o valor de c: "))

d = delta(val_a, val_b, val_c)

print("Seu delta é igual a:", d)

if d < 0:
    print("Essa equação não tem raízes reais.")
elif d == 0:
    r = -val_b / (2 * val_a)
    print("A equação tem apenas uma raiz real (raiz dupla):", r)
else:
    result1 = x1(val_a, val_b, d)
    result2 = x2(val_a, val_b, d)
    print("Acabou as continhas! Viu só, você nem cansou 😉")
    print("x1 =", result1, " | x2 =", result2)
