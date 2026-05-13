while 1: 
    ci = int(input('digite a idade 1: '))
    if ci >= 5 and ci <= 100:
        break
    else:
        print ('tente uma idade de 5 a 100')
    
while 1:
    ce = int(input('digite a idade 2: '))
    if ce >= 5 and ce <= 100:
        break
    else:
        print ('tente uma idade de 5 a 100')
    
while 1:
    ca = int(input('digite a idade 3: '))
    if ca >= 5 and ca <= 100:
        break
    else:
        print ('tente uma idade de 5 a 100')

if ca < ce and ca > ci:
    print ('camile')
if ca < ci and ca > ci:
    print ('camile')
if ce < ci and ce > ca:
    print ('cenora')
if ce < ca and ce > ci:
    print ('cenora')
if ci < ce and ci > ca:
    print ('cascalho')
if ci < ca and ci > ca:
    print ('cascalho')
