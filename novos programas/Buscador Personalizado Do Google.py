import tkinter as tk
from tkinter import ttk, scrolledtext
import webbrowser

# Lista de opções
options = [
    
  {
    "label": "GEOSINTsearch",
    "tooltip": "Searches within posts from Twitter, Reddit and 4Chan and presents anything that contains a Google Maps link",
    "value": "https://cse.google.com/cse?cx=015328649639895072395:sbv3zyxzmji"
  },
  {
    "label": "Pasted tekst",
    "tooltip": "Look if any specifc text has been posted before",
    "value": "https://cse.google.com/cse/publicurl?cx=013991603413798772546:nxs552dhq8k"
  },
  {
    "label": "Reddit GCS",
    "tooltip": None,
    "value": "https://cse.google.com/cse/publicurl?cx=017261104271573007538:bbzhlah6n4o"
  },
  {
    "label": "CSE for Telegram Data",
    "tooltip": None,
    "value": "https://cse.google.com/cse?&cx=006368593537057042503:efxu7xprihg"
  },
  {
    "label": "Brian's CSE for LinkedIn",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=005704587298353977169%3Aztqzquc6ifw"
  },
  {
    "label": "CSE for Facebook",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=016621447308871563343%3Avylfmzjmlti&fbclid=IwAR39xaF2fY-5WCxiz7YfdgxtTCztAAeWVlzz48eN6P9N_c8cYScbQJL4LGk"
  },
  {
    "label": "phone finding",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=000905274576528531678:tdnmnosylyo"
  },
  {
    "label": "Linkedin **",
    "tooltip": None,
    "value": "http://cse.google.com/cse?cx=005704587298353977169%3Aztqzquc6ifw"
  },
  {
    "label": "Social Search",
    "tooltip": "Facebook, Twitter, G+, Instagram, Linkedin, YouTUbe, Tumblr",
    "value": "http://cse.google.com/cse?cx=001580308195336108602:oyrkxatrfyq"
  },
  {
    "label": "Resume Search",
    "tooltip": None,
    "value": "http://cse.google.com/cse?cx=006262502083096379805:t6_vdxxr_xy"
  },
  {
    "label": "Slideshare Resume Search",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=009462381166450434430:vkdxe7pcnzg"
  },
  {
    "label": "Linkedin edited profile search",
    "tooltip": None,
    "value": "http://cse.google.com/cse?cx=010561883190743916877:qa_v6ioerxo#gsc.tab=0&gsc.q=java&gsc.sort=date"
  },
  {
    "label": "Yahoo groups",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=000905274576528531678:zrtxvn-hy64"
  },
  {
    "label": "Diversity Associations CSE",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=009462381166450434430:cvykemfonf4"
  },
  {
    "label": "Documents – Formats (PDF, XLSX, etc.)",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=009462381166450434430:nudphlkt3p4"
  },
  {
    "label": "CSE Google Storage",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=009462381166450434430:9eryzpq3z3a"
  },
  {
    "label": "Bitbucket",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=000905274576528531678:czs5xrlwb3m"
  },
  {
    "label": "Contactout",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=000905274576528531678:nc5j4jaxbke"
  },
  {
    "label": "Twitter list finder **",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=016621447308871563343:u4r_fupvs-e"
  },
  {
    "label": "Facebook extra Cse.google.com",
    "tooltip": "people, likes, groups, more",
    "value": "http://cse.google.com/cse?cx=016621447308871563343:vylfmzjmlti"
  },
  {
    "label": "Github **",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=017261104271573007538:fqn_jyftcdq"
  },
  {
    "label": "Reddit Google Custom Search",
    "tooltip": None,
    "value": "http://cse.google.com/cse?cx=017261104271573007538:bbzhlah6n4o"
  },
  {
    "label": "Twitter Image Search Engine",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=006290531980334157382:_ltcjq0robu"
  },
  {
    "label": "Twitter CSE by GH",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=001394533911082033616:zki7ufxkqn4"
  },
  {
    "label": "Wayup college",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=000905274576528531678:ahauktq6yim"
  },
  {
    "label": "YouTube Google Custom Search",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=004121198361051842949:uqqcf2re4ts"
  },
  {
    "label": "Developer Resumes Github Google Custom Search",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=009462381166450434430%3Afrzo6adfjso&q"
  },
  {
    "label": "Telegram 5/8/19",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=006368593537057042503:efxu7xprihg#gsc.tab=0"
  },
  {
    "label": "LinkedIn - Language Proficiency 5/9/19",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=009462381166450434430%3Adtrunj0sn4m&fbclid=IwAR2plGGkJa2OJ0TJ1oveotB5bzU2MLu2EscWW9OSZZOSHnLW53mdiiVun1A"
  },
  {
    "label": "URL Shortner Search CSE 5/15/19",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=000905274576528531678:ttpspvkuqhc"
  },
  {
    "label": "Linkedin with Contact Info CSE 5/21/19",
    "tooltip": "Curtesy of Shivkumar Gurram",
    "value": "https://cse.google.com/cse?cx=017177223831066255531%3Agw4lesi1tsw"
  },
  {
    "label": "Deloitte CSE 6/1/19",
    "tooltip": "Curetesy of Alicia Fasi!!",
    "value": "https://cse.google.com/cse?cx=000905274576528531678:szilzo9kqmy"
  },
  {
    "label": "CSE List Finder 6/3/19",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=001394533911082033616:3rmgu_htqw4"
  },
  {
    "label": "Phone Search CSE 6/4/19",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=004589886433843772608:qm0yotoa_sg"
  },
  {
    "label": "Speaker Deck CSE 7/2/19",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=010150859881542981030%3Ahqhxyxpwtc4&ie=UTF-8&q=&sa=Search"
  },
  {
    "label": "CSE Infopeople",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=002816601621090461722:3-53oxlwbos"
  },
  {
    "label": "CSE Phone Number Search",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=004589886433843772608:qm0yotoa_sg"
  },
  {
    "label": "Yahoo People Search",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=004589886433843772608:z65ypq1ip40"
  },
  {
    "label": "free people search usa",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=004589886433843772608:hrmnz8hosoa"
  },
  {
    "label": "Dating Sites",
    "tooltip": None,
    "value": "http://cse.google.com/cse/home?cx=001580308195336108602:j448_obkzkc"
  },
  {
    "label": "Mobile Search",
    "tooltip": None,
    "value": "http://cse.google.com/cse/home?cx=partner-pub-2353536094017743:1302913524&ie=UTF-8"
  },
  {
    "label": "Data.com (Jigsaw) Xray by GH",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=001394533911082033616:qxpdfivlcmg"
  },
  {
    "label": "Zoominfo and doc search",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=001788166376325824197:ff1tsbv1c6m"
  },
  {
    "label": "Dating Sites Inteltech",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=001580308195336108602:j448_obkzkc"
  },
  {
    "label": "CSE Search cBusinessCards.com",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=001334385455784943667:ktfncw2jocg"
  },
  {
    "label": "Dating Sites by Inteltechniques",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=001580308195336108602:j448_obkzkc&num=100"
  },
  {
    "label": "Email Alerts Search Engine",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=001044907178545692645:52ohlgedvaa"
  },
  {
    "label": "Emails in Resumes CSE",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=009462381166450434430:bqcc5oa64z8"
  },
  {
    "label": "CSE Email Format Finder",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=009462381166450434430:2iir9haxr-0"
  },
  {
    "label": "CSE People Search",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=009305272063906253811:0xqjdapfzsk"
  },
  {
    "label": "CSE HIdden Profiles",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=009462381166450434430:szzkoddrd6i"
  },
  {
    "label": "Email Format CSE",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=009462381166450434430:tmv95brsssm"
  },
  {
    "label": "CSE Find Emails Personal",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=000905274576528531678:hvqlnmyn2is"
  },
  {
    "label": "Google Custom Search",
    "tooltip": None,
    "value": "https://cse.google.com/cse/publicurl?cx=009462381166450434430:tmv95brsssm"
  },
  {
    "label": "Upwork CSE 5/26/19",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=000905274576528531678:ghqoq4vkvbk"
  },
  {
    "label": "Custom Search - Edit search engines.",
    "tooltip": None,
    "value": "https://cse.google.com/cse/all"
  },
  {
    "label": "Reddit - CSE",
    "tooltip": None,
    "value": "https://cse.google.com/cse/publicurl?cx=007749065626525752968:qh5bqebwi30"
  },
  {
    "label": "Google Custom Search",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=017261104271573007538:bbzhlah6n4o"
  },
  {
    "label": "CSE Linkedin/Github/Twitter Prime Diversity",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=012020006043586000305:w5dhsgzmkeg#gsc.tab=0"
  },
  {
    "label": "Emails in Resumes - CSE",
    "tooltip": None,
    "value": "https://cse.google.com/cse/publicurl?cx=009679435902400177945:inqfto9vwf4"
  },
  {
    "label": "Emails in Resumes 2 - CSE",
    "tooltip": None,
    "value": "https://cse.google.com/cse/publicurl?cx=009462381166450434430:bqcc5oa64z8"
  },
  {
    "label": "Facebook CSE",
    "tooltip": "Facebook CSE - Search Facebook for any public pages, groups or photos containing a target identifier.",
    "value": "https://cse.google.com/cse?cx=016621447308871563343:vylfmzjmlti#gsc.tab=0&gsc"
  },
  {
    "label": "Telegram CSE",
    "tooltip": "Telegago Custom Search Engine for Telegram.\nSearch a target identifier across the following Telegram categories:\n\ntelegraph\nBots\nVoice Chat\nStickers\nPublic\nPrivate\nMessages\nContacts \nVideos",
    "value": "https://cse.google.com/cse?cx=006368593537057042503:efxu7xprihg#gsc.tab=0&gsc."
  },
  {
    "label": "04/20 Benutzerdefinierte Suche - Google CSE mit Label",
    "tooltip": "Engine\n\nWie man z.B. gezielt soziale Netzwerke gebündelt oder einzeln nach Keyword durchsucht\n\nIm Google CSE neue Suche einrichten, z.B. mit\ntwitter.com / youtube.com / facebook.com / web.telegram.com\n\nDann Option linke Spalte \"Suchfunktionen\", Option \"Suchfilter\", Suchoption hinzufügen, z.B. Twitter. \"Suchfilter bearbeiten option \"Nur Websites mit diesem Labe durchsuchen\".\n\nZurück zu Startansicht, Webseite wie Twitter.com markieren, Label, Label as \"Twitter\", Apply  - fertig. Alle anderen Netzwerke ebenso verknüpfen\n\nDie CSE-Suche bietet dann Ergebnisse aus allen Netzwerken, plus separate Suche auf Twitter, FB etc",
    "value": "https://cse.google.de/"
  },
  {
    "label": "Telegram -Google Custom Search",
    "tooltip": None,
    "value": "https://cse.google.com/cse?&cx=006368593537057042503:efxu7xprihg#gsc.tab=0"
  },
  {
    "label": "TikTok Search Engine",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=011444696387487602669:aqf7d9w73om"
  },
  {
    "label": "Programmable Search Engine",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=000669844599865978955:knjzumbsqfi"
  },
  {
    "label": "Programmable Search Engine",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=009462381166450434430:9hzrh7r-6qa#gsc.tab=0"
  },
  {
    "label": "Programmable Search Engine",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=009462381166450434430:7h_-clszmyq#gsc.tab=0"
  },
  {
    "label": "Programmable Search Engine",
    "tooltip": "Latest updated profiles on Linkedin",
    "value": "https://cse.google.com/cse?cx=010561883190743916877:qa_v6ioerxo#gsc.tab=0&gsc.sort="
  },
  {
    "label": "https://cse.google.com/cse?cx=009679435902400177945:psuoqnxowx8",
    "tooltip": "LinkedIn People Finder",
    "value": "https://cse.google.com/cse?cx=009679435902400177945:psuoqnxowx8"
  },
  {
    "label": "Programmable Search Engine",
    "tooltip": "Find talent within India",
    "value": "https://cse.google.com/cse?cx=000669844599865978955:afnnjf54g4e"
  },
  {
    "label": "Dorky Google Search Engine",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=017648920863780530960:lddgpbzqgoi"
  },
  {
    "label": "OSINT Search Engine",
    "tooltip": None,
    "value": "https://cse.google.com/cse/publicurl?cx=006290531980334157382:qcaf4enph7i"
  },
  {
    "label": "People Search Engine",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=14db36e158cd791c0"
  },
  {
    "label": "Dating Sites Search Engine",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=c7b340447e1e12653"
  },
  {
    "label": "Truecaller Search Engine",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=c46b76bce1848d976"
  },
  {
    "label": "Mastodon Search Engine",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=334aec4c3c73ed945"
  },
  {
    "label": "VK Search Engine",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=f5e7cd4c6e33954ec"
  },
  {
    "label": "Facebook Photo Search",
    "tooltip": None,
    "value": "https://cse.google.com/cse/publicurl?cx=013991603413798772546:jyvyp2ppxma"
  },
  {
    "label": "Facebook Search Engine",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=95ae46262a5f2958e"
  },
  {
    "label": "Tweet Archive Search",
    "tooltip": None,
    "value": "https://cse.google.com/cse/publicurl?cx=005797772976587943970:kffjgylvzwu"
  },
  {
    "label": "Twitter List Finder",
    "tooltip": None,
    "value": "https://cse.google.com/cse/publicurl?cx=016621447308871563343:u4r_fupvs-e"
  },
  {
    "label": "Twitter Photo Search",
    "tooltip": None,
    "value": "https://cse.google.com/cse/publicurl?cx=006290531980334157382:_ltcjq0robu"
  },
  {
    "label": "Twitter Search Engine",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=5857bab69c8b8e37e"
  },
  {
    "label": "Reddit Search Engine",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=0728740ab68a619ba"
  },
  {
    "label": "LinkedIn Search Engine",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=daaf18e804f81bed0"
  },
  {
    "label": "Google+ Photo Custom Search",
    "tooltip": None,
    "value": "https://cse.google.com/cse/publicurl?cx=006205189065513216365:uo99tr1fxjq"
  },
  {
    "label": "Wordpress Blog Search",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=017261104271573007538:ffk_jpt64gy"
  },
  {
    "label": "Telegram Search",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=004805129374225513871:p8lhfo0g3hg"
  },
  {
    "label": "SEO Resources Search Engine",
    "tooltip": None,
    "value": "https://cse.google.com/cse/publicurl?cx=005797772976587943970:i7q6z1kjm1w"
  },
  {
    "label": "Mailing List Search",
    "tooltip": None,
    "value": "https://cse.google.com/cse/publicurl?cx=013991603413798772546:sipriovnbxq"
  },
  {
    "label": "Homepage Search Engine",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=005797772976587943970:3tu7im1-rdg#gsc.tab=0"
  },
  {
    "label": "Amazon Cloud Search Engine",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=005797772976587943970:g-6ohngosio#gsc.tab=0"
  },
  {
    "label": "Google CSE instances Search Engine",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=009462381166450434430:vggeu3dhhgg#gsc.tab=0"
  },
  {
    "label": "Robots.txt Search Engine",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=013991603413798772546:zu7epjqvunu"
  },
  {
    "label": "Short URL Search Engine",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=017261104271573007538:magh-vr6t6g#gsc.tab=0"
  },
  {
    "label": "Wikispaces Search Engine",
    "tooltip": None,
    "value": "https://cse.google.com/cse/publicurl?cx=005797772976587943970:afbre9pr2ly"
  },
  {
    "label": "Dog Bites Search Engine",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=partner-pub-8216357153102971:3267723418"
  },
  {
    "label": "Google Domain Hacker",
    "tooltip": None,
    "value": "https://cse.google.com/cse/publicurl?cx=005797772976587943970:ca2hiy6hmri"
  },
  {
    "label": "Google Drive Folder Search Engine",
    "tooltip": None,
    "value": "https://cse.google.com/cse/publicurl?cx=013991603413798772546:nwzqlcysx_w"
  },
  {
    "label": "Chrome Extension Archive Search Engine",
    "tooltip": None,
    "value": "https://cse.google.com/cse/publicurl?cx=000501358716561852263:h-5uyshsclq"
  },
  {
    "label": "Github with Awesome-List Search Engine",
    "tooltip": None,
    "value": "https://cse.google.com/cse/publicurl?cx=017261104271573007538:fqn_jyftcdq"
  },
  {
    "label": "Better Chrome Web Store Search Engine",
    "tooltip": None,
    "value": "https://cse.google.com/cse/publicurl?cx=006205189065513216365:pn3lumi80ne"
  },
  {
    "label": "App Store Custom Search Engine",
    "tooltip": None,
    "value": "https://cse.google.com/cse/publicurl?cx=006205189065513216365:aqogom-kfne"
  },
  {
    "label": "*.Google.com Hack Attack",
    "tooltip": None,
    "value": "https://cse.google.com/cse/publicurl?cx=017648920863780530960:lddgpbzqgoi"
  },
  {
    "label": "Search by FileType",
    "tooltip": None,
    "value": "https://cse.google.com/cse/publicurl?cx=013991603413798772546:mu-oio3a980"
  },
  {
    "label": "Search Engine Finder",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=016621447308871563343:nyvaorurd5l"
  },
  {
    "label": "Mindmap Search Engine",
    "tooltip": None,
    "value": "http://cse.google.com/cse?cx=013991603413798772546:gj6rx9spox8#gsc.tab=0"
  },
  {
    "label": "Images Search Engine",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=281566d4e61dcc05d"
  },
  {
    "label": "Photo Album Finder",
    "tooltip": None,
    "value": "https://cse.google.com/cse/publicurl?cx=013991603413798772546:bldnx392j6u"
  },
  {
    "label": "Google Docs CSE",
    "tooltip": None,
    "value": "https://cse.google.com/cse/publicurl?cx=013991603413798772546:rse-4irjrn8#gsc.tab=0"
  },
  {
    "label": "Documents Search Engine",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=e6756edc507bcfa91"
  },
  {
    "label": "Cybersec Documents Search Engine",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=013991603413798772546:ekjmizm8vus#gsc.tab=0"
  },
  {
    "label": "GoogleDrive Search Engine",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=c64ba311eb8c31896"
  },
  {
    "label": "SlideShare Search Engine",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=465eeeb114c7f523f"
  },
  {
    "label": "Pastes Search Engine",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=661713d0371832a02"
  },
  {
    "label": "Pastes Search Engine 2",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=006896442834264595052:fawrl1rug9e"
  },
  {
    "label": "GitHub Search Engine",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=1b053c8ec746d6611"
  },
  {
    "label": "Webcam Search Engine",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=013991603413798772546:gjcdtyiytey#gsc.tab=0"
  },
  {
    "label": "Bitcoin Forums Search Engine",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=f49f9d5e679b15787"
  },
  {
    "label": "CSE for Github/stackoverflow (created by Brian Fink)",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=012020006043586000305%3Aseaoylfgqio&fbclid=IwAR3UvtoLb_SM5tRjc5z3b4WUMA-81j_TyqxnWZiLuifJX7n_LH-FPDkkNKU#gsc.tab=0"
  },
  {
    "label": "Meetup CSE",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=017285398480300945862:hhjgj41fr5p"
  },
  {
    "label": "Programmable Search Engine",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=bee58a1c31f451e4a"
  },
  {
    "label": "Programmable Search Engine",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=013991603413798772546:jyvyp2ppxma#gsc.tab=0"
  },
  {
    "label": "Programmable Search Engine",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=b5bba571be1788aaa"
  },
  {
    "label": "*.Google.com Hack Attack",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=017648920863780530960%3Alddgpbzqgoi"
  },
  {
    "label": "Chrome Extension Archive Search Engine",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=000501358716561852263%3Ah-5uyshsclq"
  },
  {
    "label": "Deep Web",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=009679435902400177945%3Aqb5l2oulqhg"
  },
  {
    "label": "Document Finder",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=009679435902400177945%3Awhgvsi86pmo"
  },
  {
    "label": "Dog Bites Search Engine",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=partner-pub-8216357153102971%3A3267723418"
  },
  {
    "label": "GEOSINTsearch",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=015328649639895072395%3Asbv3zyxzmji"
  },
  {
    "label": "Github with Awesome-List Search Engine",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=017261104271573007538%3Afqn_jyftcdq"
  },
  {
    "label": "Google CSE instances Search Engine",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=009462381166450434430%3Avggeu3dhhgg#gsc.tab=0"
  },
  {
    "label": "Google Domain Hacker",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=005797772976587943970%3Aca2hiy6hmri"
  },
  {
    "label": "Google Drive Folder Search Engine",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=013991603413798772546%3Anwzqlcysx_w"
  },
  {
    "label": "Linkedin Contact Extractor",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=001394533911082033616%3Atm5y1wqwmme"
  },
  {
    "label": "Linkedin CSE",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=001394533911082033616%3Aeijeouh5qpa"
  },
  {
    "label": "Linkedin People Finder",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=009679435902400177945%3Ac__vbhhkuom"
  },
  {
    "label": "List XLS PDF",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=001394533911082033616%3Aubweltd6dqy"
  },
  {
    "label": "Obsidian Search Engine",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=e1cb686ddc9bb4236#gsc.tab=0"
  },
  {
    "label": "Pasted tekst",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=013991603413798772546%3Anxs552dhq8k"
  },
  {
    "label": "Programmable Search - Congratulations!",
    "tooltip": None,
    "value": "https://accounts.google.com/v3/signin/identifier?dsh=S-1190613080%3A1668003243293254&continue=https%3A%2F%2Fcse.google.com%2Fcse%2Fcreate%2Fcongrats%3Fcx%3D87fbaa5440fa3e4dd&gl=us&hl=en&passive=true&service=cprose&flowName=WebLiteSignIn&flowEntry=ServiceLogin&ifkv=ARgdvAsXM5f-04fap2IIvAeFS7rTH-yxxyx-pWsJS7TEC0bF-S1IcgX6VCGYphR7KRetJANwEs-xtA"
  },
  {
    "label": "Recruiters and Sourcers",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=009462381166450434430%3A1w9uqgljuvq"
  },
  {
    "label": "Reddit",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=017261104271573007538%3Abbzhlah6n4o"
  },
  {
    "label": "Robots.txt Search Engine",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=013991603413798772546%3Azu7epjqvunu"
  },
  {
    "label": "Search Engine Finder",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=016621447308871563343%3Anyvaorurd5l"
  },
  {
    "label": "CSE Document Search",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=001394533911082033616%3Afuzzaqxt_m0"
  },
  {
    "label": "CSE Document Search by format",
    "tooltip": None,
    "value": "https://cse.google.co.uk/cse?cof=CX%3ADocuments%2520-%2520Formats%3B&cx=009462381166450434430%3Anudphlkt3p4&ei=TgKvWJLJCamUgAaP1Y2IBA#=100"
  },
  {
    "label": "CSE Filetype",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=000282908376521554675%3Au17b76ejebe"
  },
  {
    "label": "CSE gutenberg Free Ebooks",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=018092787084840399530%3Ahym7amfffto"
  },
  {
    "label": "CSE PDF Search",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=001428116054185302584%3Azkwyutgabn0"
  },
  {
    "label": "CSE PubMed CSE by GH",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=001394533911082033616%3Ahb6fz4kptg8"
  },
  {
    "label": "CSE Web Based Document Hosting",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=009305272063906253811%3Agrhk5kfzv3a"
  },
  {
    "label": "Document by Format CSE",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=009462381166450434430%3Anudphlkt3p4"
  },
  {
    "label": "Google Custom Search",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=001580308195336108602%3Ahx9tv6r_od4"
  },
  {
    "label": "4archive.org",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=+017289221794755012486%3Aunlt0f39uxg"
  },
  {
    "label": "Books &amp; Publications",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=000661023013169144559%3Aa1-kkiboeco"
  },
  {
    "label": "DCox theWord Sites",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=001792384477095493274%3Ajevstkzzedu"
  },
  {
    "label": "DirectMail.com Mailing Lists",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=001920996721159070519%3A8ftyjhggvus"
  },
  {
    "label": "DivShare School Docs",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=017486593862980384588%3Awyw7npm1de4"
  },
  {
    "label": "Doc Search",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=partner-pub-3515348084564366%3A4202656657"
  },
  {
    "label": "Docs And Publications",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=007843865286850066037%3A3ajwn2jlweq"
  },
  {
    "label": "Docs Search",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=002687040058168385213%3Afybyovrsimq"
  },
  {
    "label": "docs.openhab.org",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=003707250976775348452%3Ah9hxadbatfq"
  },
  {
    "label": "Document Archieve",
    "tooltip": None,
    "value": "https://cse.google.com.au/cse?cx=partner-pub-2060328396151526%3Aea9sar-xttn"
  },
  {
    "label": "Excel",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=003792548944738135704%3Aadsi4suki70"
  },
  {
    "label": "ExcelUser.com Search Engine",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=002479282654111334943%3Ackphga52hvg"
  },
  {
    "label": "GH Loop CSE (Publications)",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=001394533911082033616%3Arzqdeqcihdm"
  },
  {
    "label": "Google File Search",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=005524257534178064433%3A43qyxjr7upa"
  },
  {
    "label": "scribd",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=013791148858571516042%3Agqsws13ehog&hl=en"
  },
  {
    "label": "Search Blogs, Docs, Help &amp; Forum",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=013315504628135767172%3Ad6shbtxu-uo&q=%25s"
  },
  {
    "label": "SEARCH BY FILETYPE",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=013991603413798772546%3Amu-oio3a980"
  },
  {
    "label": "Search by type of Documents",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=010005218567305408382%3Apz_7fcd3pr0"
  },
  {
    "label": "Typepad",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=010283551365367049042%3Aomw04pcoiyq"
  },
  {
    "label": "TYPO3",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=000230591601826276191%3Auyt_ca9wqfy"
  },
  {
    "label": "Google Doccs CSE",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=001315216799338982565%3Abdtlvsicgts&hl=en"
  },
  {
    "label": "Search for PDF CSE",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=009462381166450434430%3Aefyzyfhat50"
  },
  {
    "label": "SearchShared.com",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=004002012908077721647%3A1rl4dea84iw"
  },
  {
    "label": "Programmable Search Engine",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=006516753008110874046:1ugcdt3vo7z#gsc.tab=0"
  },
  {
    "label": "CSE General",
    "tooltip": None,
    "value": "https://cse.google.ca/cse?cx=partner-pub-0375491626617707%3A7151836262"
  },
  {
    "label": "CSE General Plus",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=018413290510798844940%3Ak69bxcfofe0"
  },
  {
    "label": "Dsmiths Custom Search Engine",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=679d31ebf4f3f4a53#gsc.tab=0"
  },
  {
    "label": "General Search CSE",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=000855927744969374910%3Atuta4di9ies"
  },
  {
    "label": "General Search Google Custom Search",
    "tooltip": None,
    "value": "https://cse.google.ca/cse?cx=partner-pub-9033736287770724%3A5710551291"
  },
  {
    "label": "Google Alerts Search Engine",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=013991603413798772546%3Ars7bbm8kdsg"
  },
  {
    "label": "Google CSE Finder",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=011081986282915606282%3Afa52ldjw5to"
  },
  {
    "label": "Google CSE Resources Search Engine",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=013991603413798772546%3Adhoqafcmphk"
  },
  {
    "label": "Carnegie Mellon University",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=000183942383624155094%3Ante7gfnbgha"
  },
  {
    "label": "DSF Google Refinement",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=002207347744245223449%3A3wxoicg4myg"
  },
  {
    "label": "General",
    "tooltip": None,
    "value": "https://cse.google.co.in/cse?cx=001639366659799729802%3Avr921b1tgry"
  },
  {
    "label": "General",
    "tooltip": None,
    "value": "https://cse.google.co.uk/cse?cx=002717229081227036262%3Ae-izaongzem"
  },
  {
    "label": "General Search",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=011545203169215625696%3A-yygy0imnne&hl=en"
  },
  {
    "label": "General Search plus",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=011507650028433360591%3Amw4qttke1oe"
  },
  {
    "label": "Google Docs Search Engine",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=013991603413798772546%3Arse-4irjrn8"
  },
  {
    "label": "Google Plus Communities CSE",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=009238533315723793042%3Aosjzdvijbbe"
  },
  {
    "label": "Google+ Collections &amp; Communities Search",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=013991603413798772546%3Ag5vjn23udla"
  },
  {
    "label": "SpeakerHub CSe 6/29/20",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=009462381166450434430%3Azhxxazdaqc4#gsc.tab=0"
  },
  {
    "label": "The Custom Search Engine CSE",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=001691553474536676049%3Aop4j-wn6tq4"
  },
  {
    "label": "URL Shortner CSE 5/15/19",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=000905274576528531678%3Attpspvkuqhc"
  },
  {
    "label": "FAS.Org Fed American Scientists",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=001482665168924075807%3Ahyits1jhoek"
  },
  {
    "label": "Free Full-Text Online Law Review/Law Journal Search Engine",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=000933248691480580078%3A57y4iyinbqe"
  },
  {
    "label": "Google Scholar CSE (Publications) by GH",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=001394533911082033616%3Awcf5spgmnbc"
  },
  {
    "label": "Mailing List Archives Search Engine",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=013991603413798772546%3Asipriovnbxq"
  },
  {
    "label": "PBWorks Search Engine",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=017261104271573007538%3Axhguhddcxuk"
  },
  {
    "label": "The Researchers Vault",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=013991603413798772546%3Afjfpayt0bje"
  },
  {
    "label": "The Search Engine Search Engine",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=013991603413798772546%3Ahvkibqdijhe"
  },
  {
    "label": "Visual Concepts CSE",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=013991603413798772546%3Agj6rx9spox8"
  },
  {
    "label": "Indeed - CSE",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=012951739560700154499%3Awq3e6dpqvt4"
  },
  {
    "label": "MTHRFCKR's MacOSX App Search",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=8741bcfbbc69912f4#gsc.tab=0"
  },
  {
    "label": "Chrome Extensions CSE",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=006205189065513216365%3Apn3lumi80ne#gsc.tab=0"
  },
  {
    "label": "CODE WITH THE FLOW",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=013991603413798772546%3Agejhsvqignk"
  },
  {
    "label": "CSE Codeforces",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=017177223831066255531%3Aj3hjrl7vxgs&q=+"
  },
  {
    "label": "CSE Github",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=017177223831066255531%3Abinmqbueqr4"
  },
  {
    "label": "CSE Github List",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=001394533911082033616%3A3rmgu_htqw4"
  },
  {
    "label": "CSE Github Research Gate",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=001394533911082033616%3Avjd-_np8_li"
  },
  {
    "label": "CSE Hackerrank",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=017177223831066255531%3Ax4sc0wrnrjc"
  },
  {
    "label": "CSE Livecode Search",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=002762050828011275793%3A09mnfq5cmmy"
  },
  {
    "label": "CSE Mobile Game Producers",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=009305272063906253811%3Ahkoxufbb8vy"
  },
  {
    "label": "CSE ReadWriteWeb Open Data search engine",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=000893276566003557773%3Ayvkihl-ixyk"
  },
  {
    "label": "CSE schema.org dev community",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=003736913799082383568%3Ac44bi0_xxek"
  },
  {
    "label": "CSE SearchDotNet Developers Search Engine",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=002213837942349435108%3Ajki1okx03jq"
  },
  {
    "label": "CSE Stack Exchange",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=017177223831066255531%3Ahvat4hdnvvy"
  },
  {
    "label": "Custom Search Engine HTAccess",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=002660089121042511758%3Akk7rwc2gx0i"
  },
  {
    "label": "Developer CSE",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=003397785032979619197%3Aqmbl_n5_etq"
  },
  {
    "label": "freecodecamp.org CSE 9/1/19",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=000905274576528531678%3Ahelqyahxtuz"
  },
  {
    "label": "Github Search +",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=017177223831066255531%3Abinmqbueqr4&q=+"
  },
  {
    "label": "Android Stuff",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=004085571554339270840%3Ah0dcfprkwsc"
  },
  {
    "label": "App Stores Search Engine",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=006205189065513216365%3Aaqogom-kfne"
  },
  {
    "label": "AWS/Dropbox/Azure Cloud +",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=002972716746423218710%3Aveac6ui3rio"
  },
  {
    "label": "C++ Search",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=000872085005376217422%3Als3uha-lskw"
  },
  {
    "label": "channel9.msdn",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=014414512506709758688%3Alw8tquo75fu"
  },
  {
    "label": "Dev",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=009828010126686317309%3A34dln55a5g4"
  },
  {
    "label": "Developer",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=007221746090449490499%3Aliubjduev9o"
  },
  {
    "label": "Development",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=010294177795457125149%3Aa6n-6zpsvz8"
  },
  {
    "label": "Development and Coding Search",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=005154715738920500810%3Afmizctlroiw"
  },
  {
    "label": "FolgerTech 2020 Custom Search Engine",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=001956934792321444063%3Akptybhr31yy"
  },
  {
    "label": "Google Developers Official",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=005326727925058575645%3Au2hfjb_gpuk"
  },
  {
    "label": "Google Operating System Blog Search:",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=003884673279755833555%3A2nd1kupam-s"
  },
  {
    "label": "Hacker News Search",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=000604492950510474204%3Anla4hxmojqu"
  },
  {
    "label": "Internet Engineering Task Force",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=006728497408158459967%3Aybxjdw-bjjw"
  },
  {
    "label": "JAVA",
    "tooltip": None,
    "value": "https://cse.google.com/cse?client=pub-8324125911897442&cof=GFNT%3A%23996699%3BGALT%3A%233333CC%3BLH%3A43%3BCX%3AJava%3BVLC%3A%23FF0000%3BDIV%3A%23996699%3BFORID%3A1%3BT%3A%23333399%3BALC%3A%23996699%3BLC%3A%23996699%3BL%3Ahttp%3A%2F%2Fjava.sun.com%2Fimages%2Fgetjava_med.gif%3BGIMP%3A%23996699%3BLP%3A1%3BBGC%3A%23FFFFFF%3BAH%3Aleft&cx=005506632761844726871%3Asmfqscqavok&sa=Search"
  },
  {
    "label": "Microsoft MSDN",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=001706605492879182808%3Ayra97xpb_7y"
  },
  {
    "label": "Open Source",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=007950368875930262986%3Avwrqfjvw_u4&hl=en"
  },
  {
    "label": "Paste Bin",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=000905274576528531678%3Azdstbilawf0"
  },
  {
    "label": "Pastebin Search GIST GITHUB",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=001580308195336108602%3Amhdmrvbspnm"
  },
  {
    "label": "Secure Sites",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=005259122747959844556%3Ag-q6xdwtlue"
  },
  {
    "label": "StackOverflow",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=004734170301196198067%3Aswzl0ra_ide"
  },
  {
    "label": "Technology &amp; Professional Development",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=000334200464811979738%3Ab0j8zmvzjnk"
  },
  {
    "label": "Test engine for pages using http://schema.org/Museum",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=003736913799082383568%3A8pkugzvixsw"
  },
  {
    "label": "The Best of Design Search",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=000834333561951534331%3Abv-yqro5krw"
  },
  {
    "label": "The Invisible Internet Project",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=013791148858571516042%3Aadxvhgecf4m&hl=en"
  },
  {
    "label": "Twisted Matrix Java",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=000092903031650492802%3Awmoqkjvon0i"
  },
  {
    "label": "Uboontu Search",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=002072379199720138921%3A9m-bgfzutzq"
  },
  {
    "label": "Xda-developers search engine",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=000825531964825142534%3Acqr2sjirilw"
  },
  {
    "label": "Pastes Search Engine 2",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=006896442834264595052%3Afawrl1rug9e"
  },
  {
    "label": "Programmable Search Engine",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=000905274576528531678%3Aczs5xrlwb3m"
  },
  {
    "label": "Raw Git Hacker",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=007791543817084091905%3Avmwkk8ksx9k"
  },
  {
    "label": "Software Code CSE",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=009462381166450434430%3A4pw19akdthg"
  },
  {
    "label": "Stackoverflow CSE",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=partner-pub-7396620608505330%3Axjbbr6-w0cu"
  },
  {
    "label": "The Code Chaser",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=013991603413798772546%3Axbbb31a0ecw"
  },
  {
    "label": "Google Map Search Engine",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=013991603413798772546%3Amofb1uoaebi"
  },
  {
    "label": "SEO Graphic Resources",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=006290531980334157382%3A3x8i6ydquuc"
  },
  {
    "label": "SEO Resources Search Engine",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=005797772976587943970%3Ai7q6z1kjm1w"
  },
  {
    "label": "Super SEO Search Engine",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=005797772976587943970%3Addxth6fexqw"
  },
  {
    "label": "The Search Engine Finder",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=013991603413798772546%3Acsa-hd4a4dk"
  },
  {
    "label": "250+ Video Sharing Sites",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=001794496531944888666%3Actbnemd5u7s"
  },
  {
    "label": "Webcam Custom Search Engine",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=013991603413798772546%3Agjcdtyiytey"
  },
  {
    "label": "OSINT Blogs Search Engine",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=fd4729049350a76d0"
  },
  {
    "label": "WordPress Content Snatcher",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=011081986282915606282%3Aw8bndhohpi0"
  },
  {
    "label": "Beautiful Photo Album Finder",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=013991603413798772546%3Abt8ybjlsnok"
  },
  {
    "label": "Clip Art",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=013097366078944830717%3Atsojriz_t1a"
  },
  {
    "label": "Clip Art Pictures",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=015775560953662364258%3Ajbn052ab538"
  },
  {
    "label": "Fotolog Photo Search Engine",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=000521750095050289010%3Azpcpi1ea4s8"
  },
  {
    "label": "Image Search",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=007197546127051102533%3Antzgmbf9hdm"
  },
  {
    "label": "Images",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=001580308195336108602%3Anjhlcftp3cs"
  },
  {
    "label": "Photo",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=011011820386761411814%3Afdioa10ovoi"
  },
  {
    "label": "Google Photo Archives Hacker",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=006205189065513216365%3Avp0ly0owiou"
  },
  {
    "label": "Google+ Photos Search Engine",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=006205189065513216365%3Auo99tr1fxjq"
  },
  {
    "label": "GooglePlus Photo Albums Search Engine",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=013991603413798772546%3A5h_z8fh4eyy"
  },
  {
    "label": "Photo Album Finder",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=013991603413798772546%3Abldnx392j6u"
  },
  {
    "label": "The Photastic Search Engine",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=017261104271573007538%3Avmpv6nt8dc4"
  },
  {
    "label": "Wallpaper Search Engine",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=006205189065513216365%3Azorwyd7ztvk"
  },
  {
    "label": "Twitter Image Search Engine",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=006205189065513216365%3Avltpvp4_gyo"
  },
  {
    "label": "Machine Learning",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=016964911540212529382%3A9j83vmmllem"
  },
  {
    "label": "Tech, Non-Tech &amp; Diversity Search Engine",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=012020006043586000305%3Aw5dhsgzmkeg#gsc.tab=0%20https://cse.google.com/cse/publicurl?cx=015211855213760009025:zpqcxcycah8%20https://cse.google.com/cse/publicurl?cx=012236071480267108189:0y1g3vhxpoe%20https://cse.google.com/cse/publicurl?cx=008789176703646299637:mubfrybi2ja"
  },
  {
    "label": "Technical Search Engine",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=000826244820084663955%3A6wz9grqlj6e"
  },
  {
    "label": "OSINT Search Engine",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=006290531980334157382%3Aqcaf4enph7i"
  },
  {
    "label": "Search Pages Start Me CSE",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=000905274576528531678:7k5elidlaww"
  },
  {
    "label": "Public Bookmarks Search",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=005797772976587943970:3tu7im1-rdg"
  },
  {
    "label": "WordPress Content Snatcher",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=011081986282915606282:w8bndhohpi0"
  },
  {
    "label": "The Ethical Hacker's Search Engine",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=009049714591083331396:dm4qfriqf3a"
  },
  {
    "label": "Google Domain Hacker",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=005797772976587943970:ca2hiy6hmri"
  },
  {
    "label": "Hacking Docs Search Engine",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=013991603413798772546:ekjmizm8vus"
  },
  {
    "label": "OSINT Tools, Resources & News Search Engine",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=006290531980334157382:qcaf4enph7i"
  },
  {
    "label": "Amazon Cloud Search Engine",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=005797772976587943970:g-6ohngosio"
  },
  {
    "label": "Top Level Domains Hacker",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=013991603413798772546:ku75d_g_s6a"
  },
  {
    "label": "US Government Intel CSE",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=009049714591083331396:i7cetsiiqru"
  },
  {
    "label": "Short URL Search Engine",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=017261104271573007538:magh-vr6t6g"
  },
  {
    "label": "OSINT CSE",
    "tooltip": None,
    "value": "http://cse.google.co.uk/cse/publicurl?cx=003089153695915392663:yi7j3xmja0w"
  },
  {
    "label": "Infosec-institute CSE",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=013991603413798772546:8c1g6f0frp8"
  },
  {
    "label": "OSINT",
    "tooltip": None,
    "value": "http://cse.google.co.uk/cse/publicurl?cx=003089153695915392663:3aeplrxqc1q"
  },
  {
    "label": "OSINT CSE",
    "tooltip": None,
    "value": "http://cse.google.com/cse/home?cx=011750002002865445766:pc60zx1rliu"
  },
  {
    "label": "CGA DIRT",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=005344331280483920295:ggl2nmh0gv0"
  },
  {
    "label": "Search any hacking activity here",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=000863474211892615554:xr1hw11tzk8"
  },
  {
    "label": "CSE Search the DIRT website archives",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=000210753555256588961:ywczj_0uvgi"
  },
  {
    "label": "ComputerCrimeInfo by Inteltechniques",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=001580308195336108602:k6lt9wtebp4"
  },
  {
    "label": "HACKERS ARISE",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=001621790233693993446:eh-n5-qfhro"
  },
  {
    "label": "CSE Malware Sample Search",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=001439139068102559330:uruncpbgqm8"
  },
  {
    "label": "CSE Hack Attack",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=016071428520527893278:3kvxtxmsfga"
  },
  {
    "label": "CSE Malware Analysis Search",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=011750002002865445766:pc60zx1rliu"
  },
  {
    "label": "CSE StackOverflow",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=011905220571137173365:7eskxxzhjj8"
  },
  {
    "label": "CSE OSINT",
    "tooltip": None,
    "value": "https://cse.google.com/cse/publicurl?cx=012209864558240645678:orirysy9yqk"
  },
  {
    "label": "Emails and resumes",
    "tooltip": None,
    "value": "http://cse.google.com/cse/home?cx=009679435902400177945:3jwfiefr024"
  },
  {
    "label": "X-Ray Profile Search use -inurl:jobs to remove job adverts.",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=007180887443585946274:cqjskbpgxum"
  },
  {
    "label": "GH Resume Finder",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=001394533911082033616:ea8vpkl6_-8"
  },
  {
    "label": "CSE HIdden Resumes",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=009462381166450434430:0aq_5piun68"
  },
  {
    "label": "GH Resume Finder",
    "tooltip": None,
    "value": "http://cse.google.com/cse?cx=001394533911082033616:ea8vpkl6_-8"
  },
  {
    "label": "Google Custom Search",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=017177223831066255531:tsl9f5keqh4"
  },
  {
    "label": "Resumes 10/11/19",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=016621447308871563343%3Avylfmzjmlti&fbclid=IwAR3ij6XCfeJjdlSQqlBwbNTEBytcb-RJ3iUk7LCN62FZ90yXtZBX8yoqIIA"
  },
  {
    "label": "Resumes 2 10/11/19",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=009462381166450434430%3Abqcc5oa64z8&fbclid=IwAR2wMk_E8K6kATeo9WwXRDsIhQEnGFD5JYW0ufCKyWmZ6yQiF5Ag5OnFjH8"
  },
  {
    "label": "CSE Facebook",
    "tooltip": None,
    "value": "http://cse.google.com/cse?cx=013639470068539630604:oqvhbt2awm8#gsc.tab=0"
  },
  {
    "label": "CSE UVRX Facebook",
    "tooltip": None,
    "value": "http://cse.google.com/cse?cx=008219812513279254587:r9bxykcq8y4"
  },
  {
    "label": "CSE Facebook Search",
    "tooltip": None,
    "value": "http://cse.google.com/cse?cx=015517404095170980323:c5nes_vjc1y"
  },
  {
    "label": "Facebook CSE",
    "tooltip": None,
    "value": "https://cse.google.com/cse/publicurl?cx=016621447308871563343:vylfmzjmlti"
  },
  {
    "label": "Facebook Search Engine",
    "tooltip": None,
    "value": "https://cse.google.com/cse/publicurl?cx=partner-pub-3873484194679120:2216860657"
  },
  {
    "label": "CSE Facebook",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=002905317608641177367:qzdk25n60gc"
  },
  {
    "label": "Gov Info Google Custom Search",
    "tooltip": None,
    "value": "http://cse.google.ca/cse/publicurl?cx=002733260306582994232:6gsdjfrruge"
  },
  {
    "label": "EDU Google Custom Search",
    "tooltip": None,
    "value": "http://cse.google.al/cse/publicurl?cx=009267560011000861900:vaap19gqdq8"
  },
  {
    "label": "Web Directory Google Custom Search",
    "tooltip": None,
    "value": "http://cse.google.co.uk/cse/home?cx=008677809312926686159:h5cfc3uroru"
  },
  {
    "label": "look4design Google Custom Search",
    "tooltip": None,
    "value": "http://cse.google.co.uk/cse/publicurl?cx=partner-pub-9952727141505497:0887073376"
  },
  {
    "label": "Internode CSE",
    "tooltip": None,
    "value": "http://cse.google.com.au/cse/publicurl?cx=016912933164822668308:-i_gzacm2xo"
  },
  {
    "label": "ACEE Google Custom Search",
    "tooltip": None,
    "value": "http://cse.google.ca/cse/publicurl?cx=002493590925847439334:_2ghogmuxfm"
  },
  {
    "label": "W3 Google Custom Search",
    "tooltip": None,
    "value": "http://cse.google.co.uk/cse/home?cx=011981465838016726163:mxtopuyuges"
  },
  {
    "label": "progresstal Google CSE",
    "tooltip": None,
    "value": "http://cse.google.co.uk/cse/publicurl?cx=013278769404190420395:bajdlveo-_y"
  },
  {
    "label": "Slide World",
    "tooltip": None,
    "value": "http://cse.google.com/cse/home?cx=002735066360616789032:vuzn6w66wc0"
  },
  {
    "label": "Dating Sites",
    "tooltip": None,
    "value": "http://cse.google.com/cse/home?cx=001580308195336108602:j448_obkzkc&num=100"
  },
  {
    "label": "Learnoutloud",
    "tooltip": None,
    "value": "http://cse.google.com/cse/home?cx=001127977917864091225:hbmbtxosnvs&hl=en"
  },
  {
    "label": "networkwaitaki.co.nz CSE",
    "tooltip": None,
    "value": "http://cse.google.co.nz/cse/publicurl?cx=010845649290979210453:ct4x_njutig"
  },
  {
    "label": "Singapore Google Custom Search",
    "tooltip": None,
    "value": "http://cse.google.com.sg/cse/publicurl?cx=003222943539432198101:zk2jr7rt4lk"
  },
  {
    "label": "Blobspot",
    "tooltip": None,
    "value": "http://cse.google.com/cse/home?cx=005290489992497281250:vnjespye2jg"
  },
  {
    "label": "Cisco",
    "tooltip": None,
    "value": "http://cse.google.com/cse/home?cx=010241283619130371030:iqtuq7sdnhq"
  },
  {
    "label": "getyourpromotionalproducts",
    "tooltip": None,
    "value": "http://cse.google.com/cse/home?cx=001823625643925212795:85kjlsp1xui"
  },
  {
    "label": "Wallpapers",
    "tooltip": None,
    "value": "http://cse.google.com.ec/cse/publicurl?cx=partner-pub-2412340340327305:1946617281"
  },
  {
    "label": "radicalreference",
    "tooltip": None,
    "value": "http://cse.google.com/cse/home?cx=012681683249965267634:qtgsi-qxlku"
  },
  {
    "label": "Network 54",
    "tooltip": None,
    "value": "http://cse.google.com/cse/home?cx=003406156692634343115:p-lxj1iav9m"
  },
  {
    "label": "Class Tools FB",
    "tooltip": None,
    "value": "http://cse.google.co.uk/cse/publicurl?cx=005467188616711423489:vg1t7c3q1q8"
  },
  {
    "label": "People Finders CSE",
    "tooltip": None,
    "value": "http://cse.google.com/cse/home?cx=002772225136813798327:om9ghdxz25e"
  },
  {
    "label": "Mobile",
    "tooltip": None,
    "value": "http://cse.google.com/cse/home?cx=007640456958190664848:-oh1odvwcd8&ie=UTF-8"
  },
  {
    "label": "AOL UK CSE",
    "tooltip": None,
    "value": "http://cse.google.com/cse/home?cx=004398262872497826460:bzd1ulmf9d0"
  },
  {
    "label": "environment CSE",
    "tooltip": None,
    "value": "http://cse.google.com/cse/home?cx=006511338351663161139:vblegi9v2au&hl=en"
  },
  {
    "label": "Think Tanks",
    "tooltip": None,
    "value": "http://cse.google.com/cse/home?cx=015174417282623600286:ixdckgldjpa"
  },
  {
    "label": "Cemetary & Obituary CSE",
    "tooltip": None,
    "value": "http://cse.google.com/cse/home?cx=003987159868624404791:_r0z_sdof4o"
  },
  {
    "label": "Mozilla Chineese",
    "tooltip": None,
    "value": "http://cse.google.com/cse/home?cx=016912487952640041581:36yox4tzlxe"
  },
  {
    "label": "BING",
    "tooltip": None,
    "value": "http://cse.google.com/cse/home?cx=013535861925762857838:eesinfdgenw"
  },
  {
    "label": "Yahoo Answers",
    "tooltip": None,
    "value": "http://cse.google.com/cse/home?cx=003997449880080175391:x2rzn8u4q1w"
  },
  {
    "label": "ASIA",
    "tooltip": None,
    "value": "http://cse.google.com/cse/home?cx=015174417282623600286:o-ftgxmhyyg&ie=UTF-8"
  },
  {
    "label": "Government",
    "tooltip": None,
    "value": "http://cse.google.com/cse/home?cx=006444040023968439261:ynbxyjszbmq"
  },
  {
    "label": "AARL Amamture radio",
    "tooltip": None,
    "value": "http://cse.google.com/cse/home?cx=010335326961734889249:ljbl2_ylmrw"
  },
  {
    "label": "Domain Search CSE",
    "tooltip": None,
    "value": "http://cse.google.com/cse/home?cx=009679435902400177945:tptqsros3w8"
  },
  {
    "label": "Newspaper & Magazine",
    "tooltip": None,
    "value": "http://cse.google.com.au/cse/publicurl?cx=010426977372765398405:3xxsh-e1cp8"
  },
  {
    "label": "Patents and Ehow",
    "tooltip": None,
    "value": "http://cse.google.com/cse/home?cx=014903090557491780498:kior4ia7n8o"
  },
  {
    "label": "Dept of Transportation",
    "tooltip": None,
    "value": "http://cse.google.com/cse/home?cx=006511338351663161139:cnk1qdck0dc&safe=on"
  },
  {
    "label": "Governent",
    "tooltip": None,
    "value": "http://cse.google.com/cse/home?cx=017167864583314760984:iecnygefhky"
  },
  {
    "label": "Super IFTTT Applet Finder",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=000501358716561852263:xzfiqchwcj8"
  },
  {
    "label": "Evidence Based Practice Search",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=000046989025241165661:sgvfxa6jyk4"
  },
  {
    "label": "History.com",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=000068555936312888960:ooeoiastmqk"
  },
  {
    "label": "CloudGofer - Search Engine for Salesforce.com v2",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=000132850124870899601:rdhrdgxtwq4"
  },
  {
    "label": "WSDOT Engineering Publications Manuals",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=000029720770544827468:itvn0p-q6nm&ie=UTF-8"
  },
  {
    "label": "Google Earth Community",
    "tooltip": None,
    "value": "http://cse.google.com/cse/home?cx=015886696515580526130:2q6y4vf4wgk"
  },
  {
    "label": "CSE Portland Transportation Search",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=000183852351473522410:be2oaa0kwzq"
  },
  {
    "label": "The Project Management Search Engine",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=000713282108823731219:o1uohgsqxsa"
  },
  {
    "label": "US Government Watchdog Sites",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=000893276566003557773:imp7zqctk60"
  },
  {
    "label": "Usability, User Interface Design and User Experience Search Engine",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=001419898076427528680:eocfus0gesw&hl=en"
  },
  {
    "label": "CSE Search TOPICS Online Magazine",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=000362978754602017392:oakcyqsw6qu"
  },
  {
    "label": "Progress & Freedom Foundation",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=000835481400639045115%3Adbc_qq-ngpa"
  },
  {
    "label": "English Grammar",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=002213090489181014274%3Apt_d7cnw9q8"
  },
  {
    "label": "Digital marketing statistics sources",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=001516306279227786131:y2bkao2c7h0"
  },
  {
    "label": "Search The Force (Salesforce)",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=001321972686981841200:-x0qn-yxszo"
  },
  {
    "label": "The IJBST Journal Index -- Index of the non-profit IJBST Journals",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=001315216799338982565:bdtlvsicgts&hl=en"
  },
  {
    "label": "Data Mining Search Engine",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=002173145610235857072:1agmeqbmpke"
  },
  {
    "label": "Unity Reference Search Engine",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=001712401338047450041:csfhqk-trfa"
  },
  {
    "label": "Sched.org Conferences CSE",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=009462381166450434430:ek3nfgkowle"
  },
  {
    "label": "CSE Excludes jobs",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=009305272063906253811:wool_g5jew4"
  },
  {
    "label": "CSE Accounting",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=009462381166450434430:txoliumsmne"
  },
  {
    "label": "CSE Career Pages",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=009462381166450434430:prm_bixv2bs"
  },
  {
    "label": "CSE Superuser",
    "tooltip": None,
    "value": "https://cse.google.com/cse?q=+&cx=017177223831066255531:agwsknarohs"
  },
  {
    "label": "CSE Tumblr",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=017177223831066255531:bm-mnya59vs"
  },
  {
    "label": "CSE Blogspot",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=017177223831066255531:5dcv0qrciug"
  },
  {
    "label": "CSE Quora",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=001394533911082033616:3ezqkoouvte"
  },
  {
    "label": "CSE G+ GH",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=001394533911082033616:svzu2yy2jqg"
  },
  {
    "label": "CSE Upwork GH",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=001394533911082033616:ldpzqnulklg"
  },
  {
    "label": "Manta GH",
    "tooltip": None,
    "value": "https://cse.google.com/cse/publicurl?cx=001394533911082033616:4g9qgau7doq"
  },
  {
    "label": "Google Custom Search",
    "tooltip": None,
    "value": "https://cse.google.com/cse/publicurl?cx=001394533911082033616:inhash9yhdk"
  },
  {
    "label": "X Ray Aboutme CSE",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=009462381166450434430:frojk6ebcay"
  },
  {
    "label": "CSE Google Scholar",
    "tooltip": None,
    "value": "https://cse.google.com/cse/publicurl?cx=009462381166450434430:aw_xfh_kydo"
  },
  {
    "label": "CSE Google Scholar GH",
    "tooltip": None,
    "value": "https://cse.google.com/cse/publicurl?cx=001394533911082033616:wcf5spgmnbc"
  },
  {
    "label": "CSE General",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=001394533911082033616:tuzl4touywm"
  },
  {
    "label": "CSE Social Search",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=000855927744969374910:tuta4di9ies"
  },
  {
    "label": "CSE Social Search",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=partner-pub-5801877696325956:4423120354"
  },
  {
    "label": "CSE Social Search",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=001580308195336108602:oyrkxatrfyq"
  },
  {
    "label": "CSE Social Search +",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=008789176703646299637:-2uxbdxhvio#gsc.tab=0"
  },
  {
    "label": "CSE Smaller Netowrk Search",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=001580308195336108602:fdcl5hqdbge"
  },
  {
    "label": "CSE General Social",
    "tooltip": None,
    "value": "https://cse.google.com/cse?q=+&cx=000282908376521554675:1nx1gjsrkqq"
  },
  {
    "label": "Company review",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=000282908376521554675:x5yj8ka4aw4"
  },
  {
    "label": "CSE Social Search",
    "tooltip": None,
    "value": "http://cse.google.com/cse?cx=014683208031386315384:yh61oezzoi8"
  },
  {
    "label": "CSE Google Social media",
    "tooltip": None,
    "value": "http://cse.google.com.au/cse?cx=010271606265296290910:zghsnbygt-w"
  },
  {
    "label": "CSE Social Media",
    "tooltip": None,
    "value": "http://cse.google.com/cse?cx=004398262872497826460:jo1ijllaj_s"
  },
  {
    "label": "CSE Social Media",
    "tooltip": None,
    "value": "http://cse.google.com/cse?cx=013791148858571516042:ntbykhk-kus"
  },
  {
    "label": "CSE WebMii",
    "tooltip": None,
    "value": "http://cse.google.com/cse?cx=010411021191781094990:fet1_l9alfu"
  },
  {
    "label": "CSE UVRX Social",
    "tooltip": None,
    "value": "http://cse.google.com/cse?cx=008219812513279254587:o2g7x-v-esw"
  },
  {
    "label": "CSE About.me",
    "tooltip": None,
    "value": "http://cse.google.co.uk/cse?cof=CX:X-Ray%2520About.me%3B&cx=009462381166450434430:frojk6ebcay&num=100&ei=oQGvWJTIDoLmgAbqv5D4Bw"
  },
  {
    "label": "CSE Slideshare",
    "tooltip": None,
    "value": "http://cse.google.co.uk/cse?cof=CX:Slideshare%2520Resumes%3B&cx=009462381166450434430:vkdxe7pcnzg&num=100&ei=kgSvWIGUKJ6vgAa25q2ADQ"
  },
  {
    "label": "Toastmasters 8/13/19",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=000905274576528531678:txzvpuasotc"
  },
  {
    "label": "Programmable Search Engine Telegram site 2/8/21",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=004805129374225513871%3Ap8lhfo0g3hg"
  },
  {
    "label": "Diversity Associations",
    "tooltip": None,
    "value": "https://cse.google.com/cse/publicurl?cx=009462381166450434430:cvykemfonf4"
  },
  {
    "label": "Diversity Sourcing",
    "tooltip": None,
    "value": "https://cse.google.com/cse/publicurl?cx=006563642812823563936:wqbm219iq-q"
  },
  {
    "label": "Tech, Non-Tech & Diversity Search Engine",
    "tooltip": None,
    "value": "https://cse.google.com/cse/publicurl?cx=012020006043586000305:w5dhsgzmkeg"
  },
  {
    "label": "Google Alerts Search Engine",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=013991603413798772546:rs7bbm8kdsg"
  },
  {
    "label": "Google Docs Search Engine",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=013991603413798772546:rse-4irjrn8"
  },
  {
    "label": "Google+ Collections & Communities Search",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=013991603413798772546:g5vjn23udla"
  },
  {
    "label": "Google Plus Communities CSE",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=009238533315723793042:osjzdvijbbe"
  },
  {
    "label": "Google CSE Resources Search Engine",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=013991603413798772546:dhoqafcmphk"
  },
  {
    "label": "Google CSE Finder",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=011081986282915606282:fa52ldjw5to"
  },
  {
    "label": "Chrome Web Store Search Engine",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=006205189065513216365:pn3lumi80ne"
  },
  {
    "label": "Google Drive Folder Search Engine",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=013991603413798772546:nwzqlcysx_w"
  },
  {
    "label": "General Search Google Custom Search",
    "tooltip": None,
    "value": "http://cse.google.ca/cse/publicurl?cx=partner-pub-9033736287770724:5710551291"
  },
  {
    "label": "The Custom Search Engine CSE",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=001691553474536676049:op4j-wn6tq4"
  },
  {
    "label": "CSE General",
    "tooltip": None,
    "value": "http://cse.google.ca/cse/publicurl?cx=partner-pub-0375491626617707:7151836262"
  },
  {
    "label": "General",
    "tooltip": None,
    "value": "http://cse.google.co.in/cse/publicurl?cx=001639366659799729802:vr921b1tgry"
  },
  {
    "label": "General",
    "tooltip": None,
    "value": "http://cse.google.co.uk/cse/publicurl?cx=002717229081227036262:e-izaongzem"
  },
  {
    "label": "General Search",
    "tooltip": None,
    "value": "http://cse.google.com/cse/home?cx=011545203169215625696:-yygy0imnne&hl=en"
  },
  {
    "label": "General Search",
    "tooltip": None,
    "value": "http://cse.google.com/cse/home?cx=006290293500274389662:a3q8k-q0xpw"
  },
  {
    "label": "General Search CSE",
    "tooltip": None,
    "value": "http://cse.google.com/cse/home?cx=000855927744969374910:tuta4di9ies"
  },
  {
    "label": "Carnegie Mellon University",
    "tooltip": None,
    "value": "http://cse.google.com/cse/home?cx=000183942383624155094:nte7gfnbgha"
  },
  {
    "label": "General Search plus",
    "tooltip": None,
    "value": "http://cse.google.com/cse/home?cx=011507650028433360591:mw4qttke1oe"
  },
  {
    "label": "CSE General Plus",
    "tooltip": None,
    "value": "http://cse.google.com/cse/home?cx=018413290510798844940:k69bxcfofe0"
  },
  {
    "label": "DSF Google Refinement",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=002207347744245223449:3wxoicg4myg"
  },
  {
    "label": "General Search Plus",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=001446049298244754897:hhkvieojx38"
  },
  {
    "label": "SpeakerHub CSe 6/29/20",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=009462381166450434430:zhxxazdaqc4#gsc.tab=0"
  },
  {
    "label": "Doximity Female Search Cse.google.com",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=009462381166450434430:spi_d6hmd9u"
  },
  {
    "label": "ResearchGate Female Search. Cse.google.com",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=009462381166450434430:tgrkurupfjk"
  },
  {
    "label": "SpeakerHub Female Search. Cse.google.com",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=009462381166450434430:zeswum8yjzw"
  },
  {
    "label": "CSE Womans name search",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=009462381166450434430%3A6lm5zrqbq1p#gsc.tab=0&gsc.sort="
  },
  {
    "label": "Social Media Search Engine",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=016621447308871563343:0p9cd3f8p-k"
  },
  {
    "label": "Data Search engine",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=002720237717066476899:v2wv26idk7m"
  },
  {
    "label": "Social Search CSE",
    "tooltip": None,
    "value": "http://cse.google.com.au/cse/publicurl?cx=010271606265296290910:zghsnbygt-w"
  },
  {
    "label": "Social Search plus",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=003001341109228051923:nfg60s0nv9a"
  },
  {
    "label": "CSE Science Search",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=002687040058168385213:fybyovrsimq"
  },
  {
    "label": "Reddit Search Engine",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=017261104271573007538:bbzhlah6n4o"
  },
  {
    "label": "Search By Site - All Social Media",
    "tooltip": None,
    "value": "https://cse.google.com/cse/publicurl?cx=011373762844405469335:vl3rlrf7ziy"
  },
  {
    "label": "Social Search CSE",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=002942036696314231120:rv-u12tedvq"
  },
  {
    "label": "Search by Site - Tumblr",
    "tooltip": None,
    "value": "https://cse.google.com/cse/publicurl?cx=011373762844405469335:bk0rpriybmc"
  },
  {
    "label": "Tapatalk CSE",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=002994322663416012776:hgqtehs5jtu"
  },
  {
    "label": "Business Research Search Engine",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=002776323165742539942:sy6ljfnnvtg"
  },
  {
    "label": "CSE SEARCH Social Networking Custom Search Engine",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=003390515112872459514:tuv0s6zg5lg"
  },
  {
    "label": "CSE Reddit",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=003602150395266240819:oc8jyzbwhag"
  },
  {
    "label": "WikiTree Free-Space Profile Search",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=003048598688029858478:e-amlq_p4my"
  },
  {
    "label": "Accelerated Search General",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=004628785839178029834:qgcgkscpg8g"
  },
  {
    "label": "Google Plus",
    "tooltip": None,
    "value": "http://cse.google.com/cse/home?cx=000991095744399886169:y2nxojqlszy"
  },
  {
    "label": "CSE InfoPathDev Search",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=003654972516704994317:4j0mji2l1rq"
  },
  {
    "label": "General Search",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=003511955876453616412%3Ap5qrqzmyezw"
  },
  {
    "label": "SEARCH Social Networking Custom Search Engine",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=003390515112872459514:tuv0s6zg5lg&hl=en%20"
  },
  {
    "label": "WikiTree Category Search",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=003048598688029858478:aemrovxydzo"
  },
  {
    "label": "Newspaper Crawling",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=003284443790305850415:xbxu60ofaec"
  },
  {
    "label": "Managing Research Data",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=005355511682543137021:knmqkoyfkrq&hl=en"
  },
  {
    "label": "CSE Freeware Search Engine",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=003865188350357615967:fq1qcs7ur94"
  },
  {
    "label": "Wikileaks CSE",
    "tooltip": None,
    "value": "http://cse.google.com/cse/home?cx=000893276566003557773:imp7zqctk60"
  },
  {
    "label": "Think Tanks",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=004976651853965360775:uqvyjatccjo"
  },
  {
    "label": "Engaged search",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=004398262872497826460:jo1ijllaj_s"
  },
  {
    "label": "welie",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=000077602365790553100:a8ekwkbphfq"
  },
  {
    "label": "Wikispaces Search Engine",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=005797772976587943970:afbre9pr2ly#gsc.tab=0"
  },
  {
    "label": "Yout Tube & Video Search",
    "tooltip": None,
    "value": "http://cse.google.com/cse/home?cx=004121198361051842949:uqqcf2re4ts"
  },
  {
    "label": "CSE IMDB",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=004747769890504554559:nckzlkyfnc0"
  },
  {
    "label": "CSE Yahoo Answers",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=003997449880080175391:x2rzn8u4q1w"
  },
  {
    "label": "Google Blogs & Press Releases Search Engine",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=005290489992497281250:vnjespye2jg"
  },
  {
    "label": "Blog Spot",
    "tooltip": None,
    "value": "http://cse.google.com/cse/home?cx=006022434428211645470:ntkymf7wi_w"
  },
  {
    "label": "Wikispaces Search engine",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=005797772976587943970:afbre9pr2ly"
  },
  {
    "label": "Google Snippet Search",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=005791863822052451275:-kbtvptt--c"
  },
  {
    "label": "Edulix Forum Search",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=005962135015314495706:z5kwyszeoi0"
  },
  {
    "label": "Government Search",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=006444040023968439261:ynbxyjszbmq"
  },
  {
    "label": "CSE Mortgage Industry",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=003346202244770019763:ea_jjt5e6mi"
  },
  {
    "label": "CSE Blogspot",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=006022434428211645470:ntkymf7wi_w"
  },
  {
    "label": "Infodio",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=004736705247395463430:hxzv8nysfmc"
  },
  {
    "label": "CSE Search Law School Websites",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=003819203596757785349:3zqblxxsu5i"
  },
  {
    "label": "Social Search",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=006289067067272019926%3Afe6cikx19js"
  },
  {
    "label": "CSE MRU Library's Canadian Academic Search Engine",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=006390257967233277436:ctqscos_st0"
  },
  {
    "label": "United States Nursery Search Engine",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=003598094056808159248:uojd4qcwnh4"
  },
  {
    "label": "Chrome Web Store Search",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=006205189065513216365:pn3lumi80ne"
  },
  {
    "label": "CSE United Kingdom search engine of search engines",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=004538409993496633550:nmlowi0wk0c"
  },
  {
    "label": "CSE Lecture Archives Search Engine",
    "tooltip": None,
    "value": "https://cse.google.com/cse/publicurl?cx=005825836113515708868:dj1m677cynu"
  },
  {
    "label": "Genealogy in Time's 46 Free of Top 100 Mega-Search Engine",
    "tooltip": None,
    "value": "http://cse.google.com/cse?cx=005825836113515708868:dj1m677cynu"
  },
  {
    "label": "Transportation Research",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=006511338351663161139:vblegi9v2au"
  },
  {
    "label": "CSE Veterans History",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=005122431749820216170:hshk5euw5uw"
  },
  {
    "label": "Greygle",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=006104376541092138401:tqbkntbyzw4&cof=FORID:1"
  },
  {
    "label": "DOAJ English Journal Content",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=005943177783402775348:0jxffbisbzk"
  },
  {
    "label": "Apache.org Mailing Lists",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=005703438322411770421:5mgshgrgx2u"
  },
  {
    "label": "US news",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=004724832962853697268:kol9sdxng2y"
  },
  {
    "label": "CSE Science Studies Search Engine",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=006369935143364481409:k8leffjphf8"
  },
  {
    "label": "Science Studies Search Engine",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=006369935143364481409%3Ak8leffjphf8"
  },
  {
    "label": "CSE Twitter",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=006649857090482600815:2gjtapmsr5y"
  },
  {
    "label": "General Search",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=004628785839178029834%3Aqgcgkscpg8g"
  },
  {
    "label": "CSE Marketing Search Engine",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=006582645638272180798:b46_olwynxm"
  },
  {
    "label": "CSE State DOT Search Engine",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=006511338351663161139:cnk1qdck0dc"
  },
  {
    "label": "Geology Search Engine",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=006290293500274389662:a3q8k-q0xpw"
  },
  {
    "label": "CSE Federal Government 2.0",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=006636090781133203169:o9hlckv9egm"
  },
  {
    "label": "CSE Resume/Bio/Profile Search",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=006262502083096379805:t6_vdxxr_xy"
  },
  {
    "label": "Twitter Image Search Engine",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=006290531980334157382:_ltcjq0robu"
  },
  {
    "label": "forum.kaspersky.com",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=005426197775070307673:n8hv9lhkp0k"
  },
  {
    "label": "Developping \".NET\" Applications",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=006259564995520986508:ehfzs0vklwk"
  },
  {
    "label": "Transportation Research Needs Meta Search",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=006511338351663161139:vblegi9v2au&hl=en"
  },
  {
    "label": "Twitter & Facebook CSE",
    "tooltip": None,
    "value": "http://cse.google.com/cse/home?cx=012389276654712134826:miiykhqamla"
  },
  {
    "label": "KNOOGLE: New Mobility Knowledge Browser",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=004787970323652826430%3Ayykh5icjh4k"
  },
  {
    "label": "Global Voices Weblog Search",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=007428522693030678892:sqmn7dng4ns"
  },
  {
    "label": "guru99 Tech",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=005996710952209167719:hnkrlqcqvwg"
  },
  {
    "label": "ColdFusion Community Search",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=007073765987311344167:ci0-oyljemw"
  },
  {
    "label": "Tweet Archive Hacker",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=005797772976587943970:kffjgylvzwu"
  },
  {
    "label": "CSE Intergovernmental Organization Search Engine",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=006748068166572874491:55ez0c3j3ey"
  },
  {
    "label": "Java related Search",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=005506632761844726871:smfqscqavok&sa=Search&cof=GFNT:%23996699%3BGALT:%233333CC%3BLH:43%3BCX:Java%3BVLC:%23FF0000%3BDIV:%23996699%3BFORID:1%3BT:%23333399%3BALC:%23996699%3BLC:%23996699%3BL:http://java.sun.com/images/getjava_med.gif%3BGIMP:%23996699%3BLP:1%3BBGC:%23FFFFFF%3BAH:left&client=pub-8324125911897442"
  },
  {
    "label": "CSE Search Weboffice",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=006865416244790422640:rzjf2tjyt70"
  },
  {
    "label": "CSE Search State Libraries",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=005450839851250975213:dkffxl8sfdw"
  },
  {
    "label": "Social",
    "tooltip": None,
    "value": "http://cse.google.com/cse/home?cx=015712187334681415946:utmijceb3ii&hl=en"
  },
  {
    "label": "CSE Oracle Blogs Search",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=006891324877144204544:kvrje889mqc"
  },
  {
    "label": "Wiki Search",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=006775555251158006122:nxp0gaipa40"
  },
  {
    "label": "CSE Google+",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=005449636645379468248:n16js_a5_yg"
  },
  {
    "label": "IETF & IRTF Mailing List Search !!!",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=006728497408158459967:ybxjdw-bjjw"
  },
  {
    "label": "CSE Microsoft Networks",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=004628785839178029834:h-wbyaybnks"
  },
  {
    "label": "FX.php Official Mailing List Archives",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=005497933486112149945:yp7frrni68w"
  },
  {
    "label": "Intergovernmental Organization Search Engine",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=006748068166572874491%3A55ez0c3j3ey"
  },
  {
    "label": "CSE real estate schools",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=005543516410900533566:6evznshwmne"
  },
  {
    "label": "Microsoft Office Tools",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=005301232024916720970:iqdlafi5ele"
  },
  {
    "label": "UN Documents",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=006289067067272019926:fe6cikx19js"
  },
  {
    "label": "GH Upwork CSE (Start Up)",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=001394533911082033616:ldpzqnulklg"
  },
  {
    "label": "Usenet Search",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=001794496531944888666:phcrapgdnqu"
  },
  {
    "label": "300+ Social Networking Sites",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=001794496531944888666:iyxger-cwug"
  },
  {
    "label": "GH Google Plus Stalker",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=001394533911082033616:svzu2yy2jqg"
  },
  {
    "label": "Social Networks Search",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=001580308195336108602:oyrkxatrfyq"
  },
  {
    "label": "Mediafire",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=001668819081665014009%3Arjwoogxyg-o"
  },
  {
    "label": "CSE GH Quora CSE",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=001394533911082033616:3ezqkoouvte"
  },
  {
    "label": "Wikileaks Search",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=001424440965645425130:0oyxt3ccoku&ie=UTF-8"
  },
  {
    "label": "Smaller Social Networks Search",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=001580308195336108602:fdcl5hqdbge"
  },
  {
    "label": "GH ZoomStalker",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=001394533911082033616%3Ainhash9yhdk"
  },
  {
    "label": "Angel List CSE (Startup) by GH",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=001394533911082033616:drafaatv8o4"
  },
  {
    "label": "GH Google Plus Stalker",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=001394533911082033616%3Asvzu2yy2jqg"
  },
  {
    "label": "Quora CSE by GH",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=001394533911082033616%3A3ezqkoouvte"
  },
  {
    "label": "Wiki CSE",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=006775555251158006122:nxp0gaipa40"
  },
  {
    "label": "CSE Toptal",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=000905274576528531678:vqpdiiu-ah0"
  },
  {
    "label": "CSE Storage",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=009462381166450434430:awjijlwzhjs"
  },
  {
    "label": "CSE Slideshare CV",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=009462381166450434430:o71s9mk6brk"
  },
  {
    "label": "Scholar Profiles CSE",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=009462381166450434430:aw_xfh_kydo"
  },
  {
    "label": "CSE HackerEarth",
    "tooltip": None,
    "value": "https://cse.google.com/cse?q=+&cx=017177223831066255531:uhdqoyq7300"
  },
  {
    "label": "CSE Behance",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=017177223831066255531:48ey6smq68a"
  },
  {
    "label": "CSE Wordpress",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=017177223831066255531:mrhnpkn_rpy"
  },
  {
    "label": "CSE Slideshare",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=017177223831066255531:ytjh2uyucva"
  },
  {
    "label": "CSE Quora",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=017177223831066255531:gez6ewf7ony"
  },
  {
    "label": "CSE Meetup",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=017177223831066255531:bifixpicxrg"
  },
  {
    "label": "CSE Visual CV",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=017177223831066255531:l-q4xo8_ou4"
  },
  {
    "label": "CSE DOYOUBUZZ",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=017177223831066255531:-2vn5fhs8da"
  },
  {
    "label": "CSE Viadeo",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=017177223831066255531:shbz951mwro"
  },
  {
    "label": "EventBright Cse.google.com",
    "tooltip": None,
    "value": "https://cse.google.com/cse/setup/basic?cx=000905274576528531678:cieeiwvzhtm"
  },
  {
    "label": "Udemy 8/16/19",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=000905274576528531678:wdu-5dklpgi"
  },
  {
    "label": "Goodreads 10/8/19",
    "tooltip": "Use it to look for people reading specific books ie Python",
    "value": "https://cse.google.com/cse?cx=000905274576528531678:suxlnoel7km"
  },
  {
    "label": "Document Archieve",
    "tooltip": None,
    "value": "http://cse.google.com.au/cse/publicurl?cx=partner-pub-2060328396151526:ea9sar-xttn"
  },
  {
    "label": "CSE Document Search",
    "tooltip": None,
    "value": "http://cse.google.com/cse?cx=001394533911082033616:fuzzaqxt_m0"
  },
  {
    "label": "CSE Document Search by format",
    "tooltip": None,
    "value": "http://cse.google.co.uk/cse?cof=CX:Documents%2520-%2520Formats;&cx=009462381166450434430:nudphlkt3p4&num=100&ei=TgKvWJLJCamUgAaP1Y2IBA"
  },
  {
    "label": "Search by type of Documents",
    "tooltip": None,
    "value": "https://cse.google.com/cse/publicurl?cx=010005218567305408382:pz_7fcd3pr0"
  },
  {
    "label": "Search Blogs, Docs, Help & Forum",
    "tooltip": None,
    "value": "https://cse.google.com/cse/publicurl?cx=013315504628135767172:d6shbtxu-uo&q=%s"
  },
  {
    "label": "Books & Publications",
    "tooltip": None,
    "value": "http://cse.google.com/cse/home?cx=000661023013169144559:a1-kkiboeco"
  },
  {
    "label": "docs.openhab.org",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=003707250976775348452:h9hxadbatfq"
  },
  {
    "label": "SearchShared.com",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=004002012908077721647:1rl4dea84iw"
  },
  {
    "label": "Google Doccs CSE",
    "tooltip": None,
    "value": "http://cse.google.com/cse/home?cx=001315216799338982565:bdtlvsicgts&hl=en"
  },
  {
    "label": "Docs Search",
    "tooltip": None,
    "value": "http://cse.google.com/cse/home?cx=002687040058168385213:fybyovrsimq"
  },
  {
    "label": "Doc Search",
    "tooltip": None,
    "value": "http://cse.google.com/cse/home?cx=009679435902400177945:whgvsi86pmo"
  },
  {
    "label": "Doc Search",
    "tooltip": None,
    "value": "http://cse.google.com/cse/home?cx=partner-pub-3515348084564366:4202656657"
  },
  {
    "label": "Google File Search",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=005524257534178064433:43qyxjr7upa"
  },
  {
    "label": "Excel",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=003792548944738135704:adsi4suki70"
  },
  {
    "label": "Docs And Publications",
    "tooltip": None,
    "value": "http://cse.google.com/cse/home?cx=007843865286850066037:3ajwn2jlweq"
  },
  {
    "label": "DivShare School Docs",
    "tooltip": None,
    "value": "http://cse.google.com/cse/home?cx=017486593862980384588:wyw7npm1de4"
  },
  {
    "label": "Typepad",
    "tooltip": None,
    "value": "http://cse.google.com/cse/home?cx=010283551365367049042:omw04pcoiyq"
  },
  {
    "label": "Lists",
    "tooltip": None,
    "value": "http://cse.google.com/cse/home?cx=008655903951728234384:p00kvkbsavm&hl=en"
  },
  {
    "label": "TYPO3",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=000230591601826276191:uyt_ca9wqfy"
  },
  {
    "label": "scribd",
    "tooltip": None,
    "value": "http://cse.google.com/cse/home?cx=013791148858571516042:gqsws13ehog&hl=en"
  },
  {
    "label": "4archive.org",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=%20017289221794755012486:unlt0f39uxg"
  },
  {
    "label": "Twisted Mailing List Archive Search",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=000092903031650492802:wmoqkjvon0i"
  },
  {
    "label": "CSE gutenberg Free Ebooks",
    "tooltip": None,
    "value": "http://cse.google.com/cse/home?cx=018092787084840399530:hym7amfffto"
  },
  {
    "label": "Ebooks Search Engine",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=000661023013169144559%3Aa1-kkiboeco"
  },
  {
    "label": "DCox theWord Sites",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=001792384477095493274:jevstkzzedu"
  },
  {
    "label": "CSE PubMed CSE by GH",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=001394533911082033616:hb6fz4kptg8"
  },
  {
    "label": "GH Loop CSE (Publications)",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=001394533911082033616:rzqdeqcihdm"
  },
  {
    "label": "DirectMail.com Mailing Lists",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=001920996721159070519:8ftyjhggvus"
  },
  {
    "label": "CSE PubPDF",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=001394533911082033616:fuzzaqxt_m0"
  },
  {
    "label": "GH List Finder CSE",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=001394533911082033616:3rmgu_htqw4"
  },
  {
    "label": "CSE PDF Search",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=001428116054185302584:zkwyutgabn0"
  },
  {
    "label": "ExcelUser.com Search Engine",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=002479282654111334943:ckphga52hvg"
  },
  {
    "label": "CSE Web Based Document Hosting",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=009305272063906253811:grhk5kfzv3a"
  },
  {
    "label": "Search for PDF CSE",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=009462381166450434430:efyzyfhat50"
  },
  {
    "label": "CSE Filetype",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=000282908376521554675:u17b76ejebe"
  },
  {
    "label": "Docs Storage",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=001580308195336108602:hx9tv6r_od4"
  },
  {
    "label": "UK CSE",
    "tooltip": None,
    "value": "http://cse.google.co.uk/cse/home?cx=partner-pub-9952727141505497:0887073376"
  },
  {
    "label": "goshah.com Japaneese",
    "tooltip": None,
    "value": "http://cse.google.co.in/cse/publicurl?cx=002761076984357676971:cu1ngn184wm"
  },
  {
    "label": "Canada Google Custom Search",
    "tooltip": None,
    "value": "http://cse.google.com.au/cse/publicurl?cx=007260874307883997617:pmakkh0eje0"
  },
  {
    "label": "UK CSE",
    "tooltip": None,
    "value": "http://cse.google.com/cse/home?cx=015544037085538061811:tfgjqzdj9ay"
  },
  {
    "label": "Twitter CSE",
    "tooltip": None,
    "value": "http://cse.google.co.uk/cse/publicurl?cx=003089153695915392663:8s9qiadkryk"
  },
  {
    "label": "Twitter Moments Search Engine",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=016621447308871563343:nuitgl_de4k"
  },
  {
    "label": "Tweet Archive Search Engine",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=013991603413798772546:h8jz6ooyjkk"
  },
  {
    "label": "CSE Twitter List finder",
    "tooltip": None,
    "value": "http://cse.google.com/cse?cx=001394533911082033616:zki7ufxkqn4"
  },
  {
    "label": "CSE UVRX Twitter",
    "tooltip": None,
    "value": "http://cse.google.com/cse?cx=008219812513279254587:bvs3qtmhtqo&cofbtnG="
  },
  {
    "label": "CSE Twitter",
    "tooltip": None,
    "value": "http://cse.google.com/cse?cx=015517404095170980323:oehnrwehzxs"
  },
  {
    "label": "Twitter",
    "tooltip": None,
    "value": "http://cse.google.com/cse/home?cx=013791148858571516042:eygbr9xc-ys"
  },
  {
    "label": "Twitter",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=003611846770411952300:sr7ajynfppc"
  },
  {
    "label": "Twitter",
    "tooltip": None,
    "value": "http://cse.google.com/cse/home?cx=013791148858571516042:mkgwsgd9da8"
  },
  {
    "label": "Twitter CSE by GH",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=001394533911082033616:zki7ufxkqn4"
  },
  {
    "label": "Twitter Historical Search",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=001439139068102559330:b1sp_fumrda"
  },
  {
    "label": "The Code Chaser",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=013991603413798772546:xbbb31a0ecw"
  },
  {
    "label": "CODE WITH THE FLOW",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=013991603413798772546:gejhsvqignk"
  },
  {
    "label": "Raw Git Hacker",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=007791543817084091905:vmwkk8ksx9k"
  },
  {
    "label": "Paste Bin",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=000905274576528531678:zdstbilawf0"
  },
  {
    "label": "Custom Search Engine HTAccess",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=002660089121042511758:kk7rwc2gx0i"
  },
  {
    "label": "Google Operating System Blog Search:",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=003884673279755833555:2nd1kupam-s"
  },
  {
    "label": "Development and Coding Search",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=005154715738920500810%3Afmizctlroiw"
  },
  {
    "label": "Test engine for pages using http://schema.org/Museum",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=003736913799082383568:8pkugzvixsw"
  },
  {
    "label": "CSE schema.org dev community",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=003736913799082383568:c44bi0_xxek"
  },
  {
    "label": "Microsoft MSDN",
    "tooltip": None,
    "value": "http://cse.google.com/cse/home?cx=001706605492879182808:yra97xpb_7y"
  },
  {
    "label": "Android Stuff",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=004085571554339270840:h0dcfprkwsc"
  },
  {
    "label": "JAVA",
    "tooltip": None,
    "value": "http://cse.google.com/cse/home?cx=005506632761844726871:smfqscqavok&sa=Search&cof=GFNT:%23996699%3BGALT:%233333CC%3BLH:43%3BCX:Java%3BVLC:%23FF0000%3BDIV:%23996699%3BFORID:1%3BT:%23333399%3BALC:%23996699%3BLC:%23996699%3BL:http://java.sun.com/images/getjava_med.gif%3BGIMP:%23996699%3BLP:1%3BBGC:%23FFFFFF%3BAH:left&client=pub-8324125911897442"
  },
  {
    "label": "Google Developers Official",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=005326727925058575645:u2hfjb_gpuk"
  },
  {
    "label": "Developer CSE",
    "tooltip": None,
    "value": "http://cse.google.com/cse/home?cx=003397785032979619197:qmbl_n5_etq"
  },
  {
    "label": "Developer",
    "tooltip": None,
    "value": "http://cse.google.com/cse/home?cx=007221746090449490499:liubjduev9o"
  },
  {
    "label": "Internet Engineering Task Force",
    "tooltip": None,
    "value": "http://cse.google.com/cse/home?cx=006728497408158459967:ybxjdw-bjjw"
  },
  {
    "label": "StackOverflow",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=004734170301196198067:swzl0ra_ide"
  },
  {
    "label": "AWS/Dropbox/Azure Cloud +",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=002972716746423218710:veac6ui3rio"
  },
  {
    "label": "Secure Sites",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=005259122747959844556:g-q6xdwtlue"
  },
  {
    "label": "Microsoft Networks",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=004628785839178029834%3Ah-wbyaybnks"
  },
  {
    "label": "Development",
    "tooltip": None,
    "value": "http://cse.google.com/cse/home?cx=010294177795457125149:a6n-6zpsvz8"
  },
  {
    "label": "CSE Livecode Search",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=002762050828011275793:09mnfq5cmmy"
  },
  {
    "label": "App Stores Search Engine",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=006205189065513216365:aqogom-kfne"
  },
  {
    "label": "Open Source",
    "tooltip": None,
    "value": "http://cse.google.com/cse/home?cx=007950368875930262986:vwrqfjvw_u4&hl=en"
  },
  {
    "label": "Twisted Matrix Java",
    "tooltip": None,
    "value": "http://cse.google.com/cse/home?cx=000092903031650492802:wmoqkjvon0i"
  },
  {
    "label": "The Invisible Internet Project",
    "tooltip": None,
    "value": "http://cse.google.com/cse/home?cx=013791148858571516042:adxvhgecf4m&hl=en"
  },
  {
    "label": "channel9.msdn",
    "tooltip": None,
    "value": "http://cse.google.com/cse/home?cx=014414512506709758688:lw8tquo75fu"
  },
  {
    "label": "Stackoverflow CSE",
    "tooltip": None,
    "value": "http://cse.google.com/cse/home?cx=partner-pub-7396620608505330:xjbbr6-w0cu"
  },
  {
    "label": "Development",
    "tooltip": None,
    "value": "http://cse.google.com/cse/home?cx=014065917776369856396:vndr2_rgcv4"
  },
  {
    "label": "Dev",
    "tooltip": None,
    "value": "http://cse.google.com/cse/home?cx=009828010126686317309:34dln55a5g4"
  },
  {
    "label": "Technology &amp; Professional Development",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=000334200464811979738:b0j8zmvzjnk"
  },
  {
    "label": "Hacker News Search",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=000604492950510474204%3Anla4hxmojqu"
  },
  {
    "label": "The Best of Design Search",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=000834333561951534331:bv-yqro5krw"
  },
  {
    "label": "Xda-developers search engine",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=000825531964825142534:cqr2sjirilw"
  },
  {
    "label": "C++ Search",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=000872085005376217422:ls3uha-lskw"
  },
  {
    "label": "Xda-developers search engine",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=000825531964825142534%3Acqr2sjirilw"
  },
  {
    "label": "Uboontu Search",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=002072379199720138921%3A9m-bgfzutzq"
  },
  {
    "label": "CSE ReadWriteWeb Open Data search engine",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=000893276566003557773:yvkihl-ixyk"
  },
  {
    "label": "CSE SearchDotNet Developers Search Engine",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=002213837942349435108:jki1okx03jq"
  },
  {
    "label": "FolgerTech 2020 Custom Search Engine",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=001956934792321444063:kptybhr31yy"
  },
  {
    "label": "Software Code CSE",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=009462381166450434430:4pw19akdthg"
  },
  {
    "label": "CSE Mobile Game Producers",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=009305272063906253811:hkoxufbb8vy"
  },
  {
    "label": "CSE Codeforces",
    "tooltip": None,
    "value": "https://cse.google.com/cse?q=+&cx=017177223831066255531:j3hjrl7vxgs"
  },
  {
    "label": "CSE Github Research Gate",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=001394533911082033616:vjd-_np8_li"
  },
  {
    "label": "CSE Stack Exchange",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=017177223831066255531:hvat4hdnvvy"
  },
  {
    "label": "CSE Hackerrank",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=017177223831066255531:x4sc0wrnrjc"
  },
  {
    "label": "freecodecamp.org CSE 9/1/19",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=000905274576528531678:helqyahxtuz"
  },
  {
    "label": "Pastebin Search GIST GITHUB",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=001580308195336108602:mhdmrvbspnm"
  },
  {
    "label": "Github Search +",
    "tooltip": None,
    "value": "https://cse.google.com/cse?q=+&cx=017177223831066255531:binmqbueqr4"
  },
  {
    "label": "CSE Github",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=017177223831066255531:binmqbueqr4"
  },
  {
    "label": "Health and Health Services Search Engine",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=002733260306582994232:vil_ukow15o"
  },
  {
    "label": "eHealthcareBot.com",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=003866911845372686500:0cgqtuu3fgc"
  },
  {
    "label": "CSE Nursing Resources Custom Search Engine",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=003418037153088753595:cudgvyhtnlu"
  },
  {
    "label": "CSE Medical Museums, Collections and Exhibitions",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=004308201683882109473:92z_qi8ylyi"
  },
  {
    "label": "Medical",
    "tooltip": None,
    "value": "http://cse.google.com/cse/home?cx=005943177783402775348:0jxffbisbzk"
  },
  {
    "label": "Austin Community College",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=005510451201798684761%3Acikyyuu9zz4"
  },
  {
    "label": "CSE Medical APPs Search (MAPPS)",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=004308201683882109473:s7kc4_l-vry"
  },
  {
    "label": "Development and Coding Search",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=005154715738920500810%3Afmizctlroiw&ie=UTF-8"
  },
  {
    "label": "Medical",
    "tooltip": None,
    "value": "http://cse.google.com/cse/home?cx=010964806533120826279:kyuedntb2fy&hl=en"
  },
  {
    "label": "DHS",
    "tooltip": None,
    "value": "http://cse.google.com/cse/home?cx=012382400048732927914:cyogm9-cln8&ie=utf-8&hl=&sa=SEARCH"
  },
  {
    "label": "Medical",
    "tooltip": None,
    "value": "http://cse.google.com/cse/home?cx=007573061199770941539:tq8w6o8sbb4"
  },
  {
    "label": "Medical",
    "tooltip": None,
    "value": "http://cse.google.com/cse/home?cx=003141222483974261931:q7fwsxdzypy"
  },
  {
    "label": "World Health Organization",
    "tooltip": None,
    "value": "http://cse.google.com/cse/home?cx=006748068166572874491%3A55ez0c3j3ey"
  },
  {
    "label": "CDC",
    "tooltip": None,
    "value": "http://cse.google.com/cse/home?cx=004668642609100521661:baynin0u0bo&hl=en"
  },
  {
    "label": "Medical/Doctors",
    "tooltip": None,
    "value": "http://cse.google.com/cse/home?cx=008693079139636136967%3Acqccx5a6mpw"
  },
  {
    "label": "CSE The Incidental Economist  The health services research blog",
    "tooltip": None,
    "value": "http://cse.google.com/cse/home?cx=012739524433329549958:qd-riv-5s98"
  },
  {
    "label": "Doctor Search",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=002171741928159552219:mq16k4juzdm"
  },
  {
    "label": "CSE Healthcare",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=009462381166450434430:pxttsuq7pw4"
  },
  {
    "label": "CSE PubMed GH",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=001394533911082033616:hb6fz4kptg8"
  },
  {
    "label": "The Photo Album Finder",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=013991603413798772546:bldnx392j6u"
  },
  {
    "label": "Twitter Image Search Engine",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=006205189065513216365:vltpvp4_gyo"
  },
  {
    "label": "Beautiful Photo Album Finder",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=013991603413798772546:bt8ybjlsnok"
  },
  {
    "label": "Google Photo Archives Hacker",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=006205189065513216365:vp0ly0owiou"
  },
  {
    "label": "The Photastic Search Engine",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=017261104271573007538:vmpv6nt8dc4"
  },
  {
    "label": "Wallpaper Search Engine",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=006205189065513216365:zorwyd7ztvk"
  },
  {
    "label": "Google+ Photos Search Engine",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=006205189065513216365:uo99tr1fxjq"
  },
  {
    "label": "GooglePlus Photo Albums Search Engine",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=013991603413798772546:5h_z8fh4eyy"
  },
  {
    "label": "Clip Art",
    "tooltip": None,
    "value": "http://cse.google.com/cse/home?cx=013097366078944830717:tsojriz_t1a"
  },
  {
    "label": "Clip Art Pictures",
    "tooltip": None,
    "value": "http://cse.google.com/cse/home?cx=015775560953662364258:jbn052ab538"
  },
  {
    "label": "Photo",
    "tooltip": None,
    "value": "http://cse.google.com/cse/home?cx=011011820386761411814:fdioa10ovoi"
  },
  {
    "label": "Image Search",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=007197546127051102533:ntzgmbf9hdm"
  },
  {
    "label": "Fotolog Photo Search Engine",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=000521750095050289010:zpcpi1ea4s8"
  },
  {
    "label": "Images",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=001580308195336108602:njhlcftp3cs"
  },
  {
    "label": "SEO Graphic Resources",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=006290531980334157382:3x8i6ydquuc"
  },
  {
    "label": "SEO Resources Search Engine",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=005797772976587943970:i7q6z1kjm1w"
  },
  {
    "label": "Super SEO Search Engine",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=005797772976587943970:ddxth6fexqw"
  },
  {
    "label": "Super IFTTT Applet Finder",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=000501358716561852263:xzfiqchwcj8"
  },
  {
    "label": "CSE SEO Resources Search Engine",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=005797772976587943970:i7q6z1kjm1w"
  },
  {
    "label": "SEO/Web",
    "tooltip": None,
    "value": "http://cse.google.com/cse/home?cx=012209517088559882238:gthoahad-m8"
  },
  {
    "label": "Webcam Custom Search Engine",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=013991603413798772546:gjcdtyiytey"
  },
  {
    "label": "250+ Video Sharing Sites",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=001794496531944888666:ctbnemd5u7s"
  },
  {
    "label": "UK Linkedin Google Custom Search",
    "tooltip": None,
    "value": "http://cse.google.co.nz/cse/publicurl?cx=014394093098352383268:w7sqo_x4rb0"
  },
  {
    "label": "CSE Linkedin Search",
    "tooltip": None,
    "value": "http://cse.google.com/cse?cx=013973300718844459208:eihyr7mwxkg"
  },
  {
    "label": "CSE Linkedin People Finder USA",
    "tooltip": None,
    "value": "http://cse.google.com/cse?cx=009679435902400177945:c__vbhhkuom"
  },
  {
    "label": "LinkedIn - Language Proficiency",
    "tooltip": None,
    "value": "https://cse.google.co.uk/cse/home?cof=CX:Language%2520Proficiency;&cx=009462381166450434430:dtrunj0sn4m&num=100&ei=SgSvWJH0EeGZgAbWzLbYCA"
  },
  {
    "label": "Finnish Linkedin CSE",
    "tooltip": None,
    "value": "https://cse.google.com/cse/publicurl?cx=018006537115644565616:hmsfwhpre5e"
  },
  {
    "label": "U.A.E. LinkedIn CSE",
    "tooltip": None,
    "value": "https://cse.google.com/cse/publicurl?cx=018006537115644565616:-j1mfiged5u"
  },
  {
    "label": "Linkedin Russian",
    "tooltip": None,
    "value": "https://cse.google.com/cse/publicurl?cx=018006537115644565616:q78kwpkrlfu"
  },
  {
    "label": "Sweden linkedin",
    "tooltip": None,
    "value": "https://cse.google.com/cse/publicurl?cx=018006537115644565616:jhdt-qmd1vc"
  },
  {
    "label": "UVRX Linkedin search",
    "tooltip": None,
    "value": "https://cse.google.com/cse/publicurl?cx=008219812513279254587:kdrphxukmpe"
  },
  {
    "label": "LinkedinMulti2017",
    "tooltip": None,
    "value": "https://cse.google.com/cse/publicurl?cx=015517404095170980323:yc0-it0uce4"
  },
  {
    "label": "Ireland",
    "tooltip": None,
    "value": "https://cse.google.com/cse/publicurl?cx=018006537115644565616:qrvhlqixq1o"
  },
  {
    "label": "Portugal",
    "tooltip": None,
    "value": "https://cse.google.com/cse/publicurl?cx=018006537115644565616:3h3hzsewsjy"
  },
  {
    "label": "Spain",
    "tooltip": None,
    "value": "https://cse.google.com/cse/publicurl?cx=018006537115644565616:rgsujyrlrk0"
  },
  {
    "label": "China",
    "tooltip": None,
    "value": "https://cse.google.com/cse/publicurl?cx=018006537115644565616:_apmupch9do"
  },
  {
    "label": "Linkedin",
    "tooltip": None,
    "value": "http://cse.google.com/cse/home?cx=012022021532202637257:ok-gfdpm_38"
  },
  {
    "label": "CSE Search UK LinkedIn Profiles",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=006639709984028990467:nl9wxsfepb0"
  },
  {
    "label": "Dutch Linkedin CSE",
    "tooltip": None,
    "value": "https://cse.google.com/cse/publicurl?cx=018006537115644565616:mhr-jonuy8u"
  },
  {
    "label": "Italy Linkedin CSE",
    "tooltip": None,
    "value": "https://cse.google.com/cse/publicurl?cx=018006537115644565616:a2127j6b8dw"
  },
  {
    "label": "Linkedin Persons CSE",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=009462381166450434430:yjqta_jasvc"
  },
  {
    "label": "Belgian LinkedIn CSE",
    "tooltip": None,
    "value": "https://cse.google.com/cse/publicurl?cx=018006537115644565616:vqp1rysqrlw"
  },
  {
    "label": "Linkedin by Country CSE",
    "tooltip": None,
    "value": "http://cse.google.com/cse/home?cx=009679435902400177945:psuoqnxowx8"
  },
  {
    "label": "Norwegian Linkedin CSE",
    "tooltip": None,
    "value": "https://cse.google.com/cse/publicurl?cx=018006537115644565616:luysxgpcp38"
  },
  {
    "label": "UK LinkedIn CSE",
    "tooltip": None,
    "value": "https://cse.google.com/cse/publicurl?cx=018006537115644565616:v0hn8800w5e"
  },
  {
    "label": "France LinkedIn CSE",
    "tooltip": None,
    "value": "https://cse.google.com/cse/publicurl?cx=018006537115644565616:g5bbve7jf4i"
  },
  {
    "label": "Germany LinkedIn CSE",
    "tooltip": None,
    "value": "https://cse.google.com/cse/publicurl?cx=018006537115644565616:9zuc1eutahe"
  },
  {
    "label": "Linkedin CSE (Created by Brian Fink) (Free)",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=005704587298353977169:ztqzquc6ifw"
  },
  {
    "label": "Japan L.I. Search",
    "tooltip": None,
    "value": "https://cse.google.com/cse/publicurl?cx=018006537115644565616:rce1dmoioac"
  },
  {
    "label": "Hong Kong L.I.",
    "tooltip": None,
    "value": "https://cse.google.com/cse/publicurl?cx=018006537115644565616:v7jcynkeife"
  },
  {
    "label": "LinkedIn - Language Proficiency",
    "tooltip": None,
    "value": "https://cse.google.co.uk/cse/publicurl?cof=CX:Language%2520Proficiency%3B&cx=009462381166450434430:dtrunj0sn4m&num=100&ei=SgSvWJH0EeGZgAbWzLbYCA"
  },
  {
    "label": "LI Email Finder",
    "tooltip": None,
    "value": "http://cse.google.com/cse?cx=000905274576528531678:lgzwvamhuvi"
  },
  {
    "label": "CSE LinkedIn X-Ray",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=002879889969213338875:ykfcyju2xe8"
  },
  {
    "label": "LinkedIn Search with Refinements",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=005704587298353977169%3Aztqzquc6ifw"
  },
  {
    "label": "CSE Linkedin",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=017177223831066255531:gw4lesi1tsw"
  },
  {
    "label": "Linkedin",
    "tooltip": None,
    "value": "http://cse.google.co.nz/cse/publicurl?cx=014394093098352383268:ckze0cnodgy"
  },
  {
    "label": "Linkedin",
    "tooltip": None,
    "value": "http://cse.google.com/cse/home?cx=011091861294247556995:u66c40virb8"
  },
  {
    "label": "Boolean String Generator",
    "tooltip": None,
    "value": "https://cse.google.com/cse/publicurl?cx=001394533911082033616:tm5y1wqwmme"
  },
  {
    "label": "Google Custom Search",
    "tooltip": None,
    "value": "https://cse.google.com/cse/publicurl?cx=001394533911082033616:eijeouh5qpa"
  },
  {
    "label": "LinkedIn - Language Proficiency",
    "tooltip": None,
    "value": "https://cse.google.com/cse/publicurl?cx=009462381166450434430:dtrunj0sn4m"
  },
  {
    "label": "LinkedIn People Finder (International)",
    "tooltip": None,
    "value": "https://cse.google.com/cse/publicurl?cx=009679435902400177945:psuoqnxowx8"
  },
  {
    "label": "Linkedin People Finder",
    "tooltip": None,
    "value": "https://cse.google.com/cse/publicurl?cx=009679435902400177945:c__vbhhkuom"
  },
  {
    "label": "Linkedin People Search",
    "tooltip": None,
    "value": "https://cse.google.com/cse/publicurl?cx=006452224553895602440:bsbhu-fdkrc"
  },
  {
    "label": "Linkedin - Profiles - CSE",
    "tooltip": None,
    "value": "https://cse.google.com/cse/publicurl?cx=009462381166450434430:dvpphoinhcg"
  },
  {
    "label": "CSE LinkedIn Résumés",
    "tooltip": None,
    "value": "https://cse.google.com/cse/publicurl?cx=010561883190743916877:qa_v6ioerxo"
  },
  {
    "label": "Social Media (Search for People on Leading Social Networking Sites)",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=000855927744969374910:tuta4di9ies"
  },
  {
    "label": "Google Custom Search",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=009462381166450434430:cvykemfonf4"
  },
  {
    "label": "CSE Linkedin Persons",
    "tooltip": None,
    "value": "http://cse.google.com/cse?cx=009462381166450434430:yjqta_jasvc"
  },
  {
    "label": "CSE Linkedin People Finder International",
    "tooltip": None,
    "value": "https://cse.google.com/cse/home?cx=009679435902400177945:psuoqnxowx8"
  },
  {
    "label": "Recruiting Live CSE",
    "tooltip": None,
    "value": "https://cse.google.com/cse/publicurl?cx=005704587298353977169:ztqzquc6ifw"
  },
  {
    "label": "US LinkedIn X-ray Search",
    "tooltip": None,
    "value": "https://cse.google.co.nz/cse/publicurl?cx=014394093098352383268:ckze0cnodgy"
  },
  {
    "label": "GH LinkedIn Contact Extractor",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=001394533911082033616:tm5y1wqwmme"
  },
  {
    "label": "GH Linkedin CSE",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=001394533911082033616:eijeouh5qpa"
  },
  {
    "label": "GH Linkedin CSE",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=001394533911082033616%3Aeijeouh5qpa"
  },
  {
    "label": "Linkedin with Refinements",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=005704587298353977169:ztqzquc6ifw"
  },
  {
    "label": "The Researcher's Vault",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=013991603413798772546:fjfpayt0bje"
  },
  {
    "label": "Visual Concepts CSE",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=013991603413798772546:gj6rx9spox8"
  },
  {
    "label": "SEARCH BY FILETYPE",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=013991603413798772546:mu-oio3a980"
  },
  {
    "label": "Find Pasted Text CSE",
    "tooltip": "Search Pastebin & Similar Sites",
    "value": "https://cse.google.com/cse?cx=013991603413798772546:nxs552dhq8k"
  },
  {
    "label": "Mailing List Archives Search Engine",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=013991603413798772546:sipriovnbxq"
  },
  {
    "label": "PBWorks Search Engine",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=017261104271573007538:xhguhddcxuk"
  },
  {
    "label": "The Search Engine Search Engine",
    "tooltip": None,
    "value": "https://cse.google.com/cse/publicurl?cx=013991603413798772546:hvkibqdijhe"
  },
  {
    "label": "ZoomInfo",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=001394533911082033616:inhash9yhdk"
  },
  {
    "label": "Free Full-Text Online Law Review/Law Journal Search Engine",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=000933248691480580078:57y4iyinbqe"
  },
  {
    "label": "Google Scholar CSE (Publications) by GH",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=001394533911082033616:wcf5spgmnbc"
  },
  {
    "label": "GH Research Gate CSE",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=001394533911082033616:vjd-_np8_li"
  },
  {
    "label": "FAS.Org Fed American Scientists",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=001482665168924075807:hyits1jhoek"
  },
  {
    "label": "CSE Data.com/Jigsaw xray GH",
    "tooltip": None,
    "value": "https://cse.google.com/cse/publicurl?cx=001394533911082033616:qxpdfivlcmg"
  },
  {
    "label": "Best Search Engine for College Students",
    "tooltip": None,
    "value": "https://cse.google.com/cse/publicurl?cx=003463032493552175486:ojqidjsvi5y"
  },
  {
    "label": "Standford University",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=003265255082301896483:sq5n7qoyfh8"
  },
  {
    "label": "CSE Teachers",
    "tooltip": None,
    "value": "http://cse.google.co.uk/cse/publicurl?cx=008631174082973208937:umykkouecka"
  },
  {
    "label": "University of Calgary",
    "tooltip": None,
    "value": "http://cse.google.ca/cse/publicurl?cx=015929661455427912796:mtcbkwv5ask&cof=FORID:0"
  },
  {
    "label": "Aalto University",
    "tooltip": None,
    "value": "http://cse.google.com.au/cse/publicurl?cx=014061069401639813104:iwagr2uihgm"
  },
  {
    "label": "Best Search Engine for College Students",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=003463032493552175486:ojqidjsvi5y"
  },
  {
    "label": "Education and Early Years: Teaching and Learning Resources and Reports",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=003565338841281719856:qw5v7bc51n8"
  },
  {
    "label": "Harvard",
    "tooltip": None,
    "value": "http://cse.google.com/cse/home?cx=005580991898689507351:lohgpyfappg"
  },
  {
    "label": "University of Missouri-St. Louis  CSE",
    "tooltip": None,
    "value": "http://cse.google.com/cse/home?cx=007678894973060939591:l0myxk63avc&hl=en"
  },
  {
    "label": "Georgia Tech Library",
    "tooltip": None,
    "value": "http://cse.google.com/cse/home?cx=007583181757493726175:8vm-y53xspk"
  },
  {
    "label": "Chabot College Library",
    "tooltip": None,
    "value": "http://cse.google.com/cse/home?cx=011960260681927197701:fzk12lxyvhw"
  },
  {
    "label": "CSE Cornell",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=000217952118062629757:xew9tb5yarq"
  },
  {
    "label": "Connecticut College",
    "tooltip": None,
    "value": "http://cse.google.com/cse/home?cx=016107364460514176754%3Al5qjc3mrgym"
  },
  {
    "label": "U.S. Universities",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=005220088828200678357:ouahf7iqawc"
  },
  {
    "label": "Education and Governemtn funded Org",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=006346700993241352089:qyczjxt9rgc"
  },
  {
    "label": "CSE OSU",
    "tooltip": None,
    "value": "http://cse.google.com.au/cse/publicurl?cx=016949707412399130039:xgwfcyee-e4"
  },
  {
    "label": "CSE OCW/OER Search Educational Searches",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=000793406067725335231:fm2ncznoswy"
  },
  {
    "label": "UTSanDiego.com Site Search",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=000525776413497593842:aooj-2z_jjm"
  },
  {
    "label": "University search",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=000790633557401345168:tgqiwagvnoy"
  },
  {
    "label": "CSE Smith College Libraries",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=001031162168201368636:xc0bxmwi9ac"
  },
  {
    "label": "University of Wisconsin–Madison",
    "tooltip": None,
    "value": "http://cse.google.com/cse/publicurl?cx=001601028090761970182:uu2tbvfp4za"
  },
  {
    "label": "Deep Web",
    "tooltip": None,
    "value": "https://cse.google.com/cse/publicurl?cx=009679435902400177945:qb5l2oulqhg"
  },
  {
    "label": "Document Finder",
    "tooltip": None,
    "value": "https://cse.google.com/cse/publicurl?cx=009679435902400177945:whgvsi86pmo"
  },
  {
    "label": "CV Searcher - Google Custom Search",
    "tooltip": None,
    "value": "https://cse.google.com/cse/publicurl?cx=009462381166450434430:0aq_5piun68"
  },
  {
    "label": "Google Custom Search",
    "tooltip": None,
    "value": "https://cse.google.com/cse/publicurl?cx=001394533911082033616:3rmgu_htqw4"
  },
  {
    "label": "List XLS PDF",
    "tooltip": None,
    "value": "https://cse.google.com/cse/publicurl?cx=001394533911082033616:ubweltd6dqy"
  },
  {
    "label": "Recruiters and Sourcers",
    "tooltip": None,
    "value": "https://cse.google.com/cse/publicurl?cx=009462381166450434430:1w9uqgljuvq"
  },
  {
    "label": "Indeed - CSE",
    "tooltip": None,
    "value": "https://cse.google.com/cse/publicurl?cx=012951739560700154499:wq3e6dpqvt4"
  },
  {
    "label": "Document Google Custom Search",
    "tooltip": None,
    "value": "https://cse.google.com/cse/publicurl?cx=000013508089310229747:qf70z1tyrs0"
  },
  {
    "label": "File Search - CSE",
    "tooltip": None,
    "value": "https://cse.google.com/cse/publicurl?cx=014863114814409449623%253Ajc-vjhl_c5g"
  },
  {
    "label": "NGO - Google Custom Search",
    "tooltip": None,
    "value": "https://cse.google.com/cse/publicurl?cx=012681683249965267634:q4g16p05-ao"
  },
  {
    "label": "Imgur - Google Custom Search",
    "tooltip": None,
    "value": "https://cse.google.com/cse/publicurl?cx=011373762844405469335:66juq46gej0"
  },
  {
    "label": "Social Media- Jonah Google Custom Search",
    "tooltip": None,
    "value": "https://cse.google.com/cse/publicurl?cx=000013508089310229747:r342wsiktms"
  },
  {
    "label": "Social Networking CSE",
    "tooltip": None,
    "value": "https://cse.google.com/cse/publicurl?cx=013791148858571516042:ntbykhk-kus"
  },
  {
    "label": "Facebook Search - CSE",
    "tooltip": None,
    "value": "https://cse.google.com/cse/publicurl?cx=partner-pub-3873484194679120%253A2216860657"
  },
  {
    "label": "Linkedin - Google Custom Search",
    "tooltip": None,
    "value": "https://cse.google.com/cse/publicurl?cx=012951739560700154499:8rl_7tkzjgq"
  },
  {
    "label": "Linkedin X-Ray - CSE",
    "tooltip": None,
    "value": "https://cse.google.com/cse/publicurl?cx=002879889969213338875:ykfcyju2xe8"
  },
  {
    "label": "Linkedin Group - Search",
    "tooltip": None,
    "value": "https://cse.google.com/cse/publicurl?cx=012022021532202637257:n0"
  },
  {
    "label": "Bitcoin - CSE",
    "tooltip": None,
    "value": "https://cse.google.com/cse/publicurl?cx=016660200577587308545:esf40ml9aag"
  },
  {
    "label": "Blade Forums",
    "tooltip": None,
    "value": "https://cse.google.com/cse/publicurl?cx=012217165931761871935:iqyc7cbzhci"
  },
  {
    "label": "Blade Forums 2 - Google Custom Search",
    "tooltip": None,
    "value": "https://cse.google.com/cse/publicurl?cx=011197018607028182644:qfobr3dlcra"
  },
  {
    "label": "Blog - CSE",
    "tooltip": None,
    "value": "https://cse.google.com/cse/publicurl?cx=007463604650659733427:mhbjfvkrs9u"
  },
  {
    "label": "Blog 2 - CSE",
    "tooltip": None,
    "value": "https://cse.google.com/cse/publicurl?cx=015539028133095552554:a7cjnp0pn-4"
  },
  {
    "label": "Blog 3 - Search",
    "tooltip": None,
    "value": "https://cse.google.com/cse/publicurl?cx=010785565387710289093%253Ajfkg3tj6dge"
  },
  {
    "label": "Blogger Hack - CSE",
    "tooltip": None,
    "value": "https://cse.google.com/cse/publicurl?cx=007997767139217218025:xiztd7bobho"
  },
  {
    "label": "Blog Posts - CSE",
    "tooltip": None,
    "value": "https://cse.google.com/cse/publicurl?cx=008280912992940796406:2loacyxhyr0"
  },
  {
    "label": "Blogspot - CSE",
    "tooltip": None,
    "value": "https://cse.google.com/cse/publicurl?cx=partner-pub-5517943437149431:9243285856"
  },
  {
    "label": "Business Research CSE",
    "tooltip": None,
    "value": "https://cse.google.com/cse/publicurl?cx=002776323165742539942:sy6ljfnnvtg"
  },
  {
    "label": "Zoom - Google Custom Search",
    "tooltip": None,
    "value": "https://cse.google.com/cse/publicurl?cx=012951739560700154499:wkgyzfjxgto"
  },
  {
    "label": "Business Exec CSE",
    "tooltip": None,
    "value": "https://cse.google.com/cse/publicurl?cx=013212718322258083429:ct_ja2rbfzo"
  },
  {
    "label": "Craigslist - CSE",
    "tooltip": None,
    "value": "https://cse.google.com/cse/publicurl?cx=008732268318596706411:nhtd4cwl5xu"
  },
  {
    "label": "Craigslist 2 CSE",
    "tooltip": None,
    "value": "https://cse.google.com/cse/publicurl?cx=010182131819082916196:wqzttyl2du0"
  },
  {
    "label": "Programmable Search Engine",
    "tooltip": None,
    "value": "https://cse.google.com/cse?q=+&cx=006368593537057042503:efxu7xprihg#gsc.tab=0&gsc.q=%20&gsc.page=1"
  },
  {
    "label": "Greg Hawkes Reddit CSE",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=001394533911082033616:cvqjwj5gxtm"
  },
  {
    "label": "LinkedIn contact search",
    "tooltip": "Custom search for contact details on LinkedIn. Created by Irina Shamaeva - booleanstrings.com/",
    "value": "https://cse.google.com/cse?cx=009462381166450434430:9hzrh7r-6qa"
  },
  {
    "label": "LinkedIn Search Engine (with Images)",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=40126f0af1aff84f8"
  },
  {
    "label": "Blogs Search Engine",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=013991603413798772546:8c1g6f0frp8#gsc.tab=0"
  },
  {
    "label": "WordPress Content Snatcher",
    "tooltip": None,
    "value": "https://cse.google.com/cse/publicurl?cx=011081986282915606282:w8bndhohpi0"
  },
  {
    "label": "News Search Engine",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=013991603413798772546:fvmtax6anhd"
  },
  {
    "label": "Slack/Discord/Zoom Invites Search",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=8e26eca532ec2cba3"
  },
  {
    "label": "Cloud Bucket Search Engine",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=d80f8518b11b1438e"
  },
  {
    "label": "Malware News Search",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=003248445720253387346:turlh5vi4xc"
  },
  {
    "label": "Google Map Search Engine",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=013991603413798772546:mofb1uoaebi"
  },
  {
    "label": "GeoINT Search",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=015328649639895072395:sbv3zyxzmji#gsc.tab=0"
  },
  {
    "label": "OFAC Sanctioned Search Engine",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=e96467889fb82b9b0"
  },
  {
    "label": "FBI Most Wanted Search Engine",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=1ee952e6584aa91f9"
  },
  {
    "label": "Interpol Most Wanted Search Engine",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=b1746754c83012613"
  },
  {
    "label": "Europol Most Wanted Search Engine",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=f08e8dc2172da1ba8"
  },
  {
    "label": "Companies & Orgs Search Engine",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=72ea9d8cfefc142d3"
  },
  {
    "label": "Europol Most Wanted Search Engine",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=f08e8dc2172da1ba8&fbclid=IwAR3ugOLPdJNySs37H8NrsR2MaJFeeGRBAKKIvlW4UfIyWILw8D1uZLSW38U"
  },
  {
    "label": "FBI most wanted search",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=1ee952e6584aa91f9&fbclid=IwAR3Oa13h7BIpEcdbpRAZDXuEJ4s8wwMGWno0-Cq3N8obnX9ZF_-SxjxJXMM"
  },
  {
    "label": "Interpol Most Wanted Search Engine",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=b1746754c83012613&fbclid=IwAR1Zk2GldNsINlgPH-4g6n9CS73XxvFyI5xiF7N2tqeAOOrAAn3X87nE-Hw"
  },
  {
    "label": "Custom Search - Create CSE",
    "tooltip": "undefined",
    "value": "https://cse.google.com/cse/create/new"
  },
  {
    "label": "Amazon Bucket Hacker",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=018215287813575168593:c17elzg384a"
  },
  {
    "label": "The Googlier Search Index",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=005797772976587943970:nixxa0prgrw"
  },
  {
    "label": "GOO.GL Search Engine",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=001691553474536676049:vpcby_api4y"
  },
  {
    "label": "Periscope/PSCP TV Search Engine",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=005797772976587943970:audysx4758e"
  },
  {
    "label": "Live Broadcasts Search Engine",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=013991603413798772546:ke-odhnab38"
  },
  {
    "label": "The Search Engine Finder",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=013991603413798772546:csa-hd4a4dk"
  },
  {
    "label": "Tech, Non-Tech & Diversity Search Engine",
    "tooltip": None,
    "value": "https://cse.google.com/cse/publicurl?cx=012020006043586000305:w5dhsgzmkeg#gsc.tab=0 https://cse.google.com/cse/publicurl?cx=015211855213760009025:zpqcxcycah8 https://cse.google.com/cse/publicurl?cx=012236071480267108189:0y1g3vhxpoe https://cse.google.com/cse/publicurl?cx=008789176703646299637:mubfrybi2ja"
  },
  {
    "label": "Technical Search Engine",
    "tooltip": None,
    "value": "https://cse.google.com/cse/publicurl?cx=000826244820084663955:6wz9grqlj6e"
  },
  {
    "label": "Machine Learning",
    "tooltip": None,
    "value": "https://cse.google.com/cse/publicurl?cx=016964911540212529382:9j83vmmllem"
  },
  {
    "label": "GoToMeeting Video Conference",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=011444696387487602669:isjgvad4bmi"
  },
  {
    "label": "Meetup Custom Search Engine",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=013991603413798772546:ego1pf6emq8"
  },
  {
    "label": "Trello Search",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=013991603413798772546:kwtsivvtnby"
  },
  {
    "label": "Livebinders E-Leaning Resources",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=013991603413798772546:65pngvxl3e4"
  },
  {
    "label": "Wikidot Search Engine",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=013991603413798772546:1tl6ugi8jja"
  },
  {
    "label": "DocumentCloud.org File Search Engine",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=011444696387487602669:o962nsq0qgk"
  },
  {
    "label": "Google Form Responses CSE",
    "tooltip": None,
    "value": "https://cse.google.com/cse?cx=011444696387487602669:ctaqbesethw"
  },
  {
    "label": "Job Search - US [ALL]",
    "tooltip": None,
    "value": "https://cse.google.com/cse/publicurl?cx=013207573749533308742:ura3u1olqiu"
  },
  {
    "label": "Job Search",
    "tooltip": None,
    "value": "https://cse.google.com/cse/publicurl?cx=partner-pub-7088803035940952:ynwgxo8bxh8"
  },
  {
    "label": "LinkedIn X-Ray",
    "tooltip": None,
    "value": "https://cse.google.com/cse/home?cx=002879889969213338875:ykfcyju2xe8"
  },
  {
    "label": "CareerSpace | Job Search..",
    "tooltip": None,
    "value": "https://cse.google.com/cse/publicurl?cx=partner-pub-4067593612301221:1623481997"
  },
  {
    "label": "Cse.google.com/cse?cx=017261104271573007538:magh-vr6t6g",
    "tooltip": None,
    "value": "http://cse.google.com/cse?cx=017261104271573007538:magh-vr6t6g"
  },
  {
    "label": "Cse.google.com/cse?cx=013991603413798772546:gj6rx9spox8",
    "tooltip": None,
    "value": "http://cse.google.com/cse?cx=013991603413798772546:gj6rx9spox8"
  },
  {
    "label": "Cse.google.com/cse?cx=005797772976587943970:g-6ohngosio",
    "tooltip": None,
    "value": "http://cse.google.com/cse?cx=005797772976587943970:g-6ohngosio"
  },
  {
    "label": "Custom Search Engine",
    "tooltip": None,
    "value": "https://cse.google.com/cse/"
  },
  {
    "label": "Google Custom Search",
    "tooltip": None,
    "value": "https://cse.google.com/cse/publicurl?cx=009462381166450434430:vkdxe7pcnzg"
  },
  {
    "label": "Google Custom Search",
    "tooltip": None,
    "value": "https://cse.google.com/cse/publicurl?cx=001394533911082033616:vjd-_np8_li"
  },
  {
    "label": "Google Custom Search",
    "tooltip": None,
    "value": "https://cse.google.com/cse/publicurl?cx=001394533911082033616:svzu2yy2jqg"
  },
  {
    "label": "Google Custom Search",
    "tooltip": None,
    "value": "https://cse.google.com/cse/publicurl?cx=001394533911082033616:hb6fz4kptg8"
  }

]

# Função para abrir o link selecionado
def open_link():
    selected_option = combo.get()
    for option in options:
        if option["label"] == selected_option:
            webbrowser.open(option["value"])
            result_text.delete(1.0, tk.END)  # Limpa o texto anterior
            result_text.insert(tk.END, f"Nome: {option['label']}\n\nLink: {option['value']}")
            break

# Configuração da interface gráfica
root = tk.Tk()
root.title("Buscador Personalizado Do Google")
root.geometry("1000x800")

# Criando o rótulo e a lista suspensa
label = tk.Label(root, text="Escolha um link", font=("TkDefaultFont", 11, "bold"))
label.pack(padx=10, pady=5)

combo = ttk.Combobox(root, values=[option["label"] for option in options], width=70)
combo.pack(padx=10, pady=5)
combo.set("GEOSINTsearch")  # Define um valor padrão

# Criando o botão para abrir o link
button = tk.Button(root, text="Abrir Link", command=open_link, bg="#23f507", font=("TkDefaultFont", 11, "bold"))
button.pack(padx=10, pady=10)

# Criando a área de texto rolável para exibir resultados
result_frame = ttk.Frame(root, padding=10)
result_frame.pack(pady=10)

result_text = scrolledtext.ScrolledText(result_frame, wrap=tk.WORD, width=130, height=35, font=("Arial", 12))
result_text.grid(column=0, row=0, sticky=tk.W, pady=15)

# Iniciando a interface gráfica
root.mainloop()
