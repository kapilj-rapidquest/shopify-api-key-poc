import sys,os
import json,re
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class Watcher:

    def __init__(self,path):
        self.observer = Observer()
        self.path = path

    def run(self):
        event_handler = Handler()
        self.observer.schedule(event_handler, self.path, recursive=True)
        self.observer.start()
        try:
            while True:
                time.sleep(10)
        except:
            self.observer.stop()
            print("Error")

        self.observer.join()


class Handler(FileSystemEventHandler):
    
    @staticmethod
    def on_any_event(event):
        if event.is_directory:
            return None

        elif event.event_type == 'created':
            # Take any action here when a file is first created.
            print("Received created event - %s." % event.src_path)

        elif event.event_type == 'modified':
            # Taken any action here when a file is modified.    
            path, fname = os.path.split(event.src_path)
            if "dist" not in path:
                print("Received modified event - %s." % event.src_path)
                global mode
                complileDir(path,mode=mode)

def strip_lines(content):
    exclude_list = [r"console\.log\(.*\);?","debugger;?"]
    m = re.search("|".join(exclude_list),content)
    if m:
        print("Found expression in exclude_list",m.group(0))
        content = content.replace(m.group(0),"") ##Replace matched with empty string
        
    return content

def compileHTML(directory,filename,mode):
    try:
        fin = os.path.join(directory, filename) 
        content = open(fin,encoding="utf8").readlines()
    except:
        return "Cannot Read Input File",directory,filename     
     
    # Show the file contents line by line.
    # We added the comma to print single newlines and not double newlines.
    # This is because the lines contain the newline character '\n'. 
    print("Got mode",mode)
    for i in range(len(content)):
        if mode != "debug":
            content[i] = strip_lines(content[i])


        if "##" not in content[i]: 
            continue

        print("found parser expression",content[i])
        
        # take everything after ## then split it by whitespace 
        try:
            expression = content[i].split("##")[1]
            command = expression.split()[0]

            loc = expression.split()[1]
            if "(" in loc:
                value = loc.split("(")[0]
                args = loc.split("(")[1].replace(")",'').strip()
                try:
                    args = json.loads(args)
                except:
                    print("Unable to parse from params",args)
                    raise Exception('Invalid params',expression)    
            else:
                value = loc
                args = {}

            print(command,value,args)
        except:
            print("Unidentified expression")
            continue    
        if command == "include":
            try:
                layout_file = os.path.join(directory, value) 
                if fin != layout_file:
                    content[i] = compileHTML(directory,value,mode)
                        
                    for key,value in args.items():
                        content[i] = content[i].replace("$"+key,value)
                #content[i] = content[i].encode('utf-8','ignore')  
                  
            except:
                print("unable to include file: ",layout_file)
                
        if command == 'if':
            statement = expression[3:]
            condition = eval(statement)

            try:
                j = 1
                while content[i+j].strip() != '##endif':
                    if not condition:
                        content[i + j] = ''
                    j += 1

                # removing if and endif
                content[i] = ''
                content[i + j] = ''
            except:
                print("Somthing went wrong in if statement", statement)

    return ''.join(content)    


def complileDir(directory,mode):    
    for filename in os.listdir(directory):

        if filename.endswith(".htmlx") or filename.endswith(".py"): 
            print(filename)

            compiledHTML = compileHTML(directory,filename,mode)
            try:     
                fout = open(directory+"/dist/"+filename.replace(".htmlx",".html"),"w+",encoding="utf8")
                fout.write(compiledHTML)       
                print("Success...")  
            except Exception as e:
                print("unable to open file",directory+"/dist/"+filename.replace(".htmlx",".html"),e)            
            
            # print()
            continue
        else:
            continue


if __name__=="__main__":
    try:
        if sys.argv[4] == "prod":
            mode = "prod"
        elif sys.argv[4] == "dev":
            mode = "dev"
        elif sys.argv[4] == "debug":
            mode = "debug"
        else:
            print("Unkown mode. use -m prod | dev | debug ",sys.argv[4] )
            sys.exit(0)
            
        if sys.argv[1] == "-w": 
            w = Watcher(sys.argv[2])
            w.run() 
        else:
            complileDir(sys.argv[2],mode)
    
    except Exception:
        print("htmlx -w[Watch] -c[Complile] directory -m[prod | dev | debug]")
        
