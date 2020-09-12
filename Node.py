import json 

#Class representing a node in the tree of nodes described in commands.json. 
class Node:

    @staticmethod
    def from_file(path:str):
        with open(path) as fp:
            return Node("root",json.load(fp))

    # You should never need to call this method. Instead use Node.from_file()
    def __init__(self,name:str,json_rep:dict):
        #The commands.json file is somewhat annoying, because the name of a node, is 
        #contained in its parrent, and not in the json object.  
        self.name = name
        assert name != "" and name != None

        #Currently the commands.json file only has these types. I don't think 
        # they are going to add more of then, but the code assumes that these 
        # are all the types
        self.type = json_rep["type"]
        assert self.type in ("literal","root","argument")
        
        

        #If a command can terminate on this node, then its executable.
        self.executable = json_rep.get("executable",False)
        assert self.executable in (True,False)

        #Only arguments have parsers
        self.parser = json_rep.get("parser",None)
        assert self.parser == None or self.type == "argument"

        #Some parsers also have properties, that modify the base parser.
        #As an example the IntegerParser could have a property that it only
        #accepts integers greather then 0. In the generated rust code, we 
        #assume those two parsers are completely different. So adding a modifier
        #results in a new parser.
        self.parser_modifier = json_rep.get("properties",None)
       

        self.children = tuple(Node(name,rep) for name,rep in json_rep.get("children",{}).items())

        #Some values are redirects to nodes elswhere in the command structure/tree. If we only follow the
        #children, then we have a spanning tree, but if we include redirects the graph can have cycles.
        #A redirect says that the "self's" children are in fact the same as the node we are redirecting to. 
        #Although there are 4-5 (ish) redirects some of them are not problematic, as they don't introduce cycles.
        #Atm.. All the "problematic" redirects are the ones pointing to the execute command. 
        #As part of this codebase we remove all redirects that are not problematic. 
        self.redirects = json_rep.get("redirect",[])

        

    def __eq__(self,other):
        if other == None:
            return False
        if type(other) != type(self):
            assert False
        return other.type == self.type and other.name == self.name and self.parser == other.parser and self.parser_modifier == other.parser_modifier and self.redirects == other.redirects

    def __hash__(self):
        return hash((self.name,self.type,self.parser,str(self.parser_modifier)))

    def __str__(self):
        if self.parser:
            return str({"name": self.name, "type": self.type, "parser": self.parser,"modifier": self.parser_modifier})
        else:
            return str({"name": self.name, "type": self.type})

    #Iterates over children, but not redirects
    def __iter__(self):
        for childe in self.children:
            yield from childe
        yield self

    def find(self,name) -> "Node":
        results = [x for x in self if x.name == name]

        if len(results) == 0:
            assert False
            return None,
        elif len(results) == 1:
            return results[0]
        else:
            #We assume the nodes name is unique.
            assert False
    
    #Iterates over nodes that "self" redirects to, irregardless if it points to a node that has
    #self as one of its children / grand/ grand..grand-children.
    def redirects_itr(self,root:"Node"):
        for name in self.redirects:
            n = root.find(name)
            if n:
                yield n
    
    
    def parrent_to(self,other):
        return any(x == other for x in self)

    
    # Parsers are actually never given a name in commands.json, instead we must add them manually.
    # To do this we add a file Parser.py to contain a mapping from the id of the parser to its name. 
    @property
    def parser_id(self):
        assert self.type == "argument" #Only parsers have parser id's
        return self.parser + str(self.parser_modifier)
        
    #  
    #
    def remove_unessesary_redirects(self,root:"Node"=None):
        if not root:
            root = self
        
        for redirect in tuple(self.redirects_itr(root)):
            if not redirect.parrent_to(self):
                self.children = self.children + redirect.children
                self.redirects = tuple(x for x in self.redirects if x != redirect.name)

        for node in self.children:
            node.remove_unessesary_redirects(root)
    

    def to_json(self):
        data = {}
        
        data["type"] = self.type
        data["name"] = self.name
        data["executable"] = self.executable

        data["redirects"] = self.redirects
        data["children"] = tuple(map(lambda x: x.to_json(),self.children))

        if self.type == "argument":
            data["parser"] = {
                "parser" : self.parser,
                "modifier" : self.parser_modifier 
            }
        

        return data

        
    def all_parsers(self, parsers=None):
        if parsers == None:
            parsers = []
        
        if self.type == "argument":
            parser = {
                "parser" : self.parser,
                "modifier" : self.parser_modifier 
            }
            if not parser in parsers:
                parsers.append(parser)
            
        for node in self:
            if node != self:
                node.all_parsers(parsers)

        return parsers
        


        
        

if __name__ == "__main__":
    
    n = Node.from_file("../commands.json")
    n.remove_unessesary_redirects(n)

    i = 0
    for node in n:
        i += 1
        if node.redirects and "execute" not in node.redirects:
            print(node,node.redirects,node.children)

    with open("new_commands.json","w") as fp:
        json.dump(n.to_json(),fp,indent=1)


    print(len(n.all_parsers()))

    