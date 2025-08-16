class Niko:
    def __init__(self, id, name, description):
        self.id = id
        self.name = name
        self.description = description

def niko_convert(s: tuple):
    id, name, description = s[0], s[1], s[2]
    return Niko(id, name, description)