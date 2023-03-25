#include <iostream>
#include <string>
#include <cstdlib>
#include <cstdio>

using namespace std;

int main()
{
    string url;
    cout << "\nDigite a URL do site: ";
    getline(cin, url);

    /* Para pular uma linha em C++, você pode usar o caractere especial de escape: cout << "\n";  */
    cout << "\n";

    string command = "curl -s --head -A \"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36\" " + url;
    
    FILE *fp = popen(command.c_str(), "r");
    if (fp == nullptr) {
        cerr << "Erro ao executar o comando" << endl;
        return 1;
    }

    char buffer[128];
    while (fgets(buffer, sizeof(buffer), fp) != nullptr) {
        cout << buffer;
    }

    pclose(fp);
    return 0;
}
