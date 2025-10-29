#include <stdio.h>
#include <stdlib.h>

void texto(){
    printf ("Hello Word");
}

int soma(){
    int num1, num2, resultado;
    
    printf ("digite o primeiro numero: ");
    scanf("%d", &num1);
    
    
    printf ("digite o segundo numero: ");
    scanf("%d", &num2);
    
   
    resultado = num1 + num2;
    
    printf ("o resultado da soma de %d e %d é igual a %d" , num1 , num2 , resultado);
    
    return 0;
}

int rep(){
    int indice = 10;
    
    do{
        printf("%d", indice);
        indice++;
    }while (indice >= 100);
    
    return 0;
    
}
    
int main (){
    
    for (int i = 0; ; i++){
        printf("%d \n" , i);
        if (i == 50){
            return 0;
        else
    }
    }
}

    
