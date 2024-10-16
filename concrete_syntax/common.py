from lark import Transformer

def indent(multiline_string, how_much):
    lines = multiline_string.split('\n')
    return '\n'.join([' '*how_much+l for l in lines])

def display_value(val: any, type_name: str, indentation=0):
    if type_name == "ActionCode":
        if '\n' in val:
            return '```\n'+indent(val, indentation+4)+'\n'+' '*indentation+'```'
        else:
            return '`'+val+'`'
    elif type_name == "String":
        return '"'+val+'"'
    elif type_name == "Integer" or type_name == "Boolean":
        return str(val)
    else:
        raise Exception("don't know how to display value" + type_name)


# internal use only
# just a dumb wrapper to distinguish between code and string
class _Code:
   def __init__(self, code):
      self.code = code

class TBase(Transformer):

    def IDENTIFIER(self, token):
        return str(token)
    
    def INT(self, token):
        return int(token)

    def BOOL(self, token):
        return token == "True"

    def STR(self, token):
        return str(token[1:-1]) # strip the "" or ''

    def CODE(self, token):
        return _Code(str(token[1:-1])) # strip the ``

    def INDENTED_CODE(self, token):
        skip = 4 # strip the ``` and the following newline character
        space_count = 0
        while token[skip+space_count] == " ":
            space_count += 1
        lines = token.split('\n')[1:-1]
        for line in lines:
            if len(line) >= space_count and line[0:space_count] != ' '*space_count:
                raise Exception("wrong indentation of INDENTED_CODE")
        unindented_lines = [l[space_count:] for l in lines]
        return _Code('\n'.join(unindented_lines))

    def literal(self, el):
        return el[0]