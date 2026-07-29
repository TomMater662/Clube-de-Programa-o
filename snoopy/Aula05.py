num1 = (int(input(':')))
num2 = []
i = 1
while 1:
    x = num1 // i
    if x > 0:
        i = i * 10
    else:
        i = i // 10
        break
while num1 > 0:
    num2.append (num1//i)
    num1 = num1 % i
    i = i // 10
print(num2)
