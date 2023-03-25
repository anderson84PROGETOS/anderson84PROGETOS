#include <iostream>
#include <fstream>
#include <netdb.h>
#include <arpa/inet.h>
#include <cstring>
#include <string>
#include <vector>

using namespace std;

vector<string> load_wordlist(const string& filename) {
    vector<string> wordlist;
    ifstream file(filename);

    if (!file.is_open()) {
        cerr << "Não foi possível abrir o arquivo " << filename << endl;
        return wordlist;
    }

    string line;
    while (getline(file, line)) {
        wordlist.push_back(line);
    }

    file.close();
    return wordlist;
}

int main(int argc, char* argv[]) {
    if (argc < 2) {
        cerr << "Por favor, digite a URL do website." << endl;
        return 1;
    }

    string url = argv[1];
    struct hostent* host = gethostbyname(url.c_str());

    if (host == NULL) {
        cerr << "Não foi possível obter informações do host." << endl;
        return 2;
    }

    cout << "Endereços IP para " << url << ":" << endl;
    for (int i = 0; host->h_addr_list[i] != NULL; i++) {
        struct in_addr address;
        memcpy(&address, host->h_addr_list[i], sizeof(address));
        cout << inet_ntoa(address) << endl;
    
    }

    cout << endl << "\nEncontrar subdomínios usando wordlist...\n" << endl;
    vector<string> wordlist = load_wordlist("wordlist.txt");
    for (const string& word : wordlist) {
        string subdomain = word + "." + url;
        struct hostent* sub_host = gethostbyname(subdomain.c_str());

        if (sub_host != NULL) {
            cout << "Subdomínio encontrado: " << subdomain << endl;
        }
    }

    return 0;
}
