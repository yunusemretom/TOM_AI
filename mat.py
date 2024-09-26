a = int(input("sayı gir: "))

while True:
    print(a)
    if a % 2 == 0:
        a=a/2
    elif a == 1:
        break
    else:
        a = 3*a+1
    
    