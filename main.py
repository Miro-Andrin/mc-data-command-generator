import os, sys, hashlib,subprocess, json, shutil
from pathlib import Path
from Node import Node
from Parser import ParserMapping
try:
    import requests

except:
    print("Failed to import requests. Have you installed it with 'pip3 install requests'?")
    sys.exit(1)

try:
    import jsonschema
except:
    print("Failed to imprt jsonschema. Have you installed it with 'pip3 install jsonschema'?")
    sys.exit(1)

Links = {

    "1.13"   : "https://launcher.mojang.com/v1/objects/d0caafb8438ebd206f99930cfaecfa6c9a13dca0/server.jar",
    "1.13.1" : "https://launcher.mojang.com/v1/objects/fe123682e9cb30031eae351764f653500b7396c9/server.jar",
    "1.13.2" : "https://launcher.mojang.com/v1/objects/3737db93722a9e39eeada7c27e7aca28b144ffa7/server.jar",
    "1.14"   : "https://launcher.mojang.com/v1/objects/f1a0073671057f01aa843443fef34330281333ce/server.jar",
    "1.14.1" : "https://launcher.mojang.com/v1/objects/ed76d597a44c5266be2a7fcd77a8270f1f0bc118/server.jar",
    "1.14.2" : "https://launcher.mojang.com/v1/objects/808be3869e2ca6b62378f9f4b33c946621620019/server.jar",
    "1.14.3" : "https://launcher.mojang.com/v1/objects/d0d0fe2b1dc6ab4c65554cb734270872b72dadd6/server.jar",
    "1.14.4" : "https://launcher.mojang.com/v1/objects/3dc3d84a581f14691199cf6831b71ed1296a9fdf/server.jar",
    "1.15"   : "https://launcher.mojang.com/v1/objects/e9f105b3c5c7e85c7b445249a93362a22f62442d/server.jar",
    "1.15.1" : "https://launcher.mojang.com/v1/objects/4d1826eebac84847c71a77f9349cc22afd0cf0a1/server.jar",
    "1.15.2" : "https://launcher.mojang.com/v1/objects/bb2b6b1aefcd70dfd1892149ac3a215f6c636b07/server.jar",
    "1.16"   : "https://launcher.mojang.com/v1/objects/a0d03225615ba897619220e256a266cb33a44b6b/server.jar",
    "1.16.1" : "https://launcher.mojang.com/v1/objects/a412fd69db1f81db3f511c1463fd304675244077/server.jar",
    "1.16.2" : "https://launcher.mojang.com/v1/objects/c5f6fb23c3876461d46ec380421e42b289789530/server.jar",
    "1.16.3" : "https://launcher.mojang.com/v1/objects/f02f4473dbf152c23d7d484952121db0b36698cb/server.jar"


}


#Check that java is installed
compledted_prosess = subprocess.run(args = ["java","--version"],capture_output=True,text=True)
if not compledted_prosess.returncode == 0:
    print(compledted_prosess.stdout)
    print(compledted_prosess.stderr)
    print(f"Could not run the command 'java --version', got returncode {compledted_prosess.returncode}. Is it installed?")





folder = Path(__file__).parent 

if not os.path.exists(folder / "./mc-data/"):
    os.mkdir(folder / "./mc-data/")


for version, link in Links.items():
    if not os.path.exists(folder / f"./mc-data/{version}"):
        os.mkdir(folder / f"./mc-data/{version}")

    server_jar = folder / f"./mc-data/{version}/server.jar"

    if not os.path.exists(server_jar):
        print(f"Downloading {version} into {server_jar}")
        with open(server_jar, "wb") as fp:
            r = requests.get(link)

            if r.status_code  != 200:
                print(f"ERROR: status code = {r.status_code}")
                sys.exit(1)
            
            fp.write(r.content)


    #Check that sha1 in the link equals the sha1 of the file
    with open(server_jar, "rb") as fp:
        #print(f"Checking sha1 of {version} server.jar")
        sha1 = hashlib.sha1()
        while True:
            data = fp.read(65536) #bufferd reading
            if not data:
                break
            sha1.update(data)

        
        assert link.startswith("https://launcher.mojang.com/v1/objects/") and link.endswith("/server.jar")
        expected_sha1 = link[39:-11]
        computed_sha1 = sha1.hexdigest()
        
        if expected_sha1 != computed_sha1:
            print(f"The computed sha1 {computed_sha1} != expected {expected_sha1}")
            print(f"You should probably delete the file: {server_jar} and run this program again.")
            sys.exit(1)



    # Extract data if not present
    if not os.path.exists(folder / f"./mc-data/{version}/generated/reports/commands.json"):
        compledted_prosess = subprocess.run(args=["java","-cp","server.jar","net.minecraft.data.Main", "--reports"],cwd=folder / f"./mc-data/{version}/")

        compledted_prosess.check_returncode()



    

for version in Links.keys():

    n = Node.from_file(folder / f"./mc-data/{version}/generated/reports/commands.json")
    n.remove_unessesary_redirects(n)

    # Get the parser mapping. This lets us add the extra data about every parser. Here we
    # can add stuff like testcases so that its easier to implement a parser propperly.
    parsers = n.all_parsers()
    mapping = ParserMapping(parsers)

    data = {
        "root" : n.to_json(),
        "parsers" : mapping.to_json()
    }

    with open(folder / f"./mc-data/{version}/commands.json","w") as fp:
        json.dump(data,fp,indent=1)


for version in Links.keys():

    #Now we validate that generated commands.json follows the schema
    if not os.path.exists(folder / f"./commands_schema.json"):
        print("Could not find the command.schema file that should be in the same folder as mc-downloader.py!") 
        sys.exit(1)

    with open(folder / "./commands_schema.json","r") as fp:
        schema = json.load(fp)
    
    with open(folder / f"./mc-data/{version}/commands.json","r") as fp:
        instance = json.load(fp)


    try:
        jsonschema.validate(instance,schema)

    except Exception as e:
        print(e)
        print(f"Failed to validate ./mc-data/{version}/commands.json to match commands_schema.json" )
        sys.exit(1)

    
print("Done generating data, evey commands.json generated and validated agains schema!")
print("The imporoved commands.json files can be found in ./mc-data/{version}/commands.json")
print("Moving data to minecraft-data if possible.")

for mc_version in Links.keys():
    # Check that every mc version has a folder in minecraft-data
    if not os.path.exists(folder / f"./minecraft-data/data/pc/{mc_version}"):
        print(f"Warning minecraft-data does not have a folder for {mc_version}")
        continue
    
    
    shutil.copyfile(folder / f"mc-data/{version}/commands.json",folder / f"minecraft-data/data/pc/{mc_version}/commands.json")


shutil.copyfile(folder / f"commands_schema.json",folder / "minecraft-data/schemas/commands_schema.json")