# This file contains code that adds info about every parser. This info is optional and 
# must be edited manually, as it is not present in minecraft. 
# This information is usefull when implementing the different parsers, 
import json, os
from pathlib import Path

class ParserMapping:

    def __init__(self,parsers:list):

        self.parsers = parsers

        if not os.path.exists(Path(__file__).parent / "./config/parsers.json"):
            self.data = {}
        else:
            with open(Path(__file__).parent / "./config/parsers.json", "r") as fp:
                self.data = json.load(fp)

        # Add all new parsers to parsers.json
        for parser in parsers:
            id = str(parser["parser"])
            if parser["modifier"]:
                id = id + str(parser["modifier"])
            if id not in self.data.keys():
                self.data[id] =  {
                    "examples" : [],
                    "regex" : ""
                }

        with open(Path(__file__).parent / "./config/parsers.json", "w") as fp:
            json.dump(self.data,fp,sort_keys=True,indent=1)
        

    def to_json(self):

        arr = []
        for parser in self.parsers:

            id = str(parser["parser"])
            if parser["modifier"]:
                id = id + str(parser["modifier"])
            
            if self.data[id]:
                data = {
                    "parser" : parser["parser"],
                    "modifier" : parser["modifier"],
                    "examples" :  self.data[id]["examples"],
                }
            else:
                data = {
                    "parser" : parser["parser"],
                    "modifier" : parser["modifier"],
                    "examples" :  [],
                }
            
            arr.append(data)
    
        return arr