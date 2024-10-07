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
