version = "2r"

# Needed for pre-import check
import subprocess,sys

# Import check / installer -----

install = False
try:
    import requests,json,re
    from termcolor import colored
except ImportError:
    install = True
    print("Missing some dependencies!")
    print("Do you want to install them now?")
    print("This will attempt to install the followimg packages to *your* python installation: requests, termcolor")
    answer = input("Y/N >")
    if not answer.upper() == "Y":
        print("No packages were installed")
        exit()
    print("Installing requests")
    subprocess.check_call([sys.executable, "-m", "pip", "install", 'requests'])
    print("Installing termcolor")
    subprocess.check_call([sys.executable, "-m", "pip", "install", 'termcolor'])
finally:
    try:
        import requests,json,re
        from termcolor import colored
        if install:
            print()
            print("Imported succesfully! (You should not be required to do this again)")
    except ImportError:
        print("Failed to import... Try doing it manually")


# Program starts here ----

global commands,msghelp

def remove_html(text):
    clean = re.compile('<.*?>')
    return re.sub(clean, '', text)

def search(term,nresults=5):
    term = term.replace(" ","_")
    url = f"https://www.snl.no/api/v1/search?query={term}&limit={nresults}"
    return json.loads(requests.get(url).content)

def clamp(v,miv,mav): # Simple clamping function
    if v<miv:v=miv
    elif v>mav:v=mav
    return v

def display_results(jsondata,nterms=5): #Display search results from json response
    global links_forlater
    links_forlater = []
    if len(jsondata) > 0:
        for i in range(0,clamp(nterms,1,len(jsondata))):
            print()
            srank = round(jsondata[i]["rank"])
            if srank < 500:
                print(str(i)+" - "+remove_html(jsondata[i]["title"])+" - s-score:"+colored(str(srank),"red"))
            else:
                print(str(i)+" - "+remove_html(jsondata[i]["title"])+" - s-score:"+colored(str(srank),"green"))

            links_forlater.append(jsondata[i]["permalink"])
            print(remove_html(jsondata[i]["first_two_sentences"]))
            if i < 1:
                print("----- Snippet:")
                print(remove_html(jsondata[i]["snippet"]))
                print("-----")
    else:
        print()
        print(colored("Search returned no results","red"))

def print_article(data): # Print an entire article
    print("--------")
    print(remove_html(data["title"].capitalize()))
    print(remove_html(data["url"]))
    print("--------")
    print()
    if remove_html(data["xhtml_body"]).strip("\n").startswith("er"):
        print(remove_html(data["title"].capitalize())+" "+remove_html(data["xhtml_body"]).strip("\n"))
    else:
        print(remove_html(data["xhtml_body"]).strip("\n"))

def get_article(name): # Tries to get an article from all subdomains
    name = name.replace(" ","_")
    url = f"https://www.snl.no/{name}.json"
    try:
        response = json.loads(requests.get(url).content)
        print_article(response)
    except json.decoder.JSONDecodeError:
        url = f"https://sml.snl.no/{name}.json"
        try:
            response = json.loads(requests.get(url).content)
            print_article(response)
        except json.decoder.JSONDecodeError:
            url = f"https://nbl.snl.no/{name}.json"
            try:
                response = json.loads(requests.get(url).content)
                print_article(response)
            except json.decoder.JSONDecodeError:
                url = f"https://meta.snl.no/{name}.json"
                try:
                    response = json.loads(requests.get(url).content)
                    print_article(response)
                except json.decoder.JSONDecodeError:
                    print(colored(f"Error loading article: {name}.json ... Attempting to search instead.","red"))
                    resp = search(name,1)
                    try:
                        url = resp[0]["article_url_json"]
                        rank = resp[0]["rank"]
                        response = json.loads(requests.get(url).content)
                        if rank < 500:
                            print(colored("Low search rank. Article might not be accurate","yellow"))
                        print_article(response)
                    except IndexError:
                        print(colored("No results found. (Article names are case sensitive, did you type it in correctly?)","red"))
                    #print(colored(f"Error loading article: {name} (Article names are case sensitive, did you type it in correctly?)","red"))

def parse_command(command,argumentmode=False,arguments=[],entirearg=[]): #This is very hacky and probably unstable...
    #command = command.upper().strip(" ")
    if command in commands:
        if command == "H":
            print(msghelp)
        elif command == "A":
            if argumentmode:
                name = entirearg.strip()
            else:    
                print(colored("Type the article name","blue"))
                name = str(input(">"))
            get_article(name)
        elif command == "S":
            if argumentmode:
                q = entirearg.strip()
            else:
                print(colored("Type search query","blue"))
                q = str(input(">"))
            print(f"Search results for {q}")
            display_results(search(q),5)
        elif command == "Q":
            exit()
        elif command == "M":
            if argumentmode:
                tin = entirearg.split(",")
            else:
                print(colored("Type in a comma separated list of terms","blue"))
                tin = str(input(">")).split(",")
                print(colored("Working...","grey"))
            results = []
            for a in tin:
                data = search(a.strip(),1)
                if len(data)>0:
                    text = data[0]["first_two_sentences"]+"\n"+data[0]["article_url"]
                else:
                    text = colored("No results...","red")
                results.append(text)

            print(colored("This tool only checks the first result returned by search and therefore, the information given might not be correct!","yellow"))
            for i,text in enumerate(results):
                print(tin[i]) 
                print(text)
                print()
    else:
        try:
            if int(command) >= 0 and int(command) <= 4:
                try:
                    get_article(links_forlater[int(command)])
                except NameError or ValueError:
                    print(colored("Please perform a search first!","blue"))
            else:
                print(colored("Unrecognized command! ('H' to see a list of commands)","red"))
        except ValueError:
            print(colored("Unrecognized command! ('H' to see a list of commands)","red"))
    print()

commands = ["A","S","H","Q","M"]

msghelp = f"""
SNLtool v{version}
wryhode 2023

Show this menu          - H
Article by name         - A
Search for article      - S
    After seartching you
    can type a number 0-4
    to immediately load
    that article
Multisearch for summarys- M
Quit                    - Q

Commands support arguments e.g >s DNA or >a Fisk
SNLtool also supports startup arguments for single
operations.

Need more help? Want to report a bug?
DM me on discord: wryhode#0674

Powered by Store Norske Leksikon's free API
Please do not use this tool for nefarious purposes!
(API-spamming, DoS Attacks or similar)

Notice on licenses:
Some articles might be protected for redistribution
by a license. SNLtool does not check that. Before
using any information this program returns, please
check what licence the article in question is 
protected by."""

if len(sys.argv) > 1: # Startup arguments, quit afterwards
    args = ""
    for arg in sys.argv:
        args += arg+" "
    parse_command(sys.argv[1].upper(),True,sys.argv,args.split(" ",2)[2])
    exit()

# Intro screen
print(colored("SNLtool","yellow"))
print(colored("wryhode2023","yellow"))
print("Enter H for help")

while True:
    command = str(input(">"))
    if len(command.split(" "))>1: # With arguments
        cmdlist = [""]+command.split(" ")
        parse_command(cmdlist[1].upper(),True,cmdlist,command.split(" ",1)[1]) # Help me what am I even doing?
    else:
        parse_command(command.upper())