


class CvObject:

    def __init__(self , children):
        self.children = []

    def decode(self):
        for child in self.children :
            child.decode()

class MultiChildCvObject (CvObject):
    
    def __init__(self , children):
        self.children = children
    def decode(self):
        for child in self.children :
            child.decode()
    
class SingleChildCvObject (CvObject):
    
    def __init__(self , child):
        self.child = child

    def decode(self):
        self.child.decode()

class Section(MultiChildCvObject):

    title = ""
    children = []
    
    def __init__(self, title, children):
        self.title = title
        self.children = children
    
    def decode(self):

        for child in self.children :
            child.decode()

class SubSection(MultiChildCvObject):

    title = ""
    children = []
    
    def __init__(self, title, children):
        self.title = title
        self.children = children

class Paragraph(SingleChildCvObject):
    pass

class ListItem(SingleChildCvObject):
    pass

class List(MultiChildCvObject):
    pass

class Link(SingleChildCvObject):
    pass

class Image(SingleChildCvObject):
    pass
