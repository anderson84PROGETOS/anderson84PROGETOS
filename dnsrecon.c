#include <string.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/types.h>
#include <arpa/inet.h>
#include <netdb.h>

int main(int argc, char *argv[])
{
	char *alvo;
	alvo = argv[1];
	struct hostent *host;
	char *result;
	char txt[50];
	FILE *recon;
	recon = fopen(argv[2],"r");
	
	if(argc < 2)
	{
	printf("|-|-|-|-|-|-|-|-|-|-|-|-|-|-|-|-|-|-|-|-|-|-|-|-|-|-|-|-|-|-|-|-|-|-|\n");
	printf("|-|-|-|-|-|-|-|-|-|-|-|-|-|-|-|-|-|-|-|-|-|-|-|-|-|-|-|-|-|-|-|-|-|-|\n");
	printf("|-|-|-|-|-|-|-|-|Uso:./dnsrecon exemplo.com recon.txt |-|-|-|-|-|-|-|\n");
	printf("|-|-|-|-|-|-|-|-|Compilar: gcc dnsrecon.c -o dnsrecon |-|-|-|-|-|-|-|\n");
	printf("|-|-|-|-|-|-|-|-|-|-|-|-|-|-|-|-|-|-|-|-|-|-|-|-|-|-|-|-|-|-|-|-|-|-|\n");
	return(0);
	}

	while(fscanf(recon, "%s", &txt) != EOF)
		{
		result = (char *) strcat(txt,alvo);
		host=gethostbyname(result);
		if(host == NULL)
		{	
		continue;
		}
		printf("HOST ENCONTRADO: %s ====> IP: %s \n", result, inet_ntoa(*((struct in_addr *)host->h_addr)));
		}
}




