# based on https://stackoverflow.com/a/39381428
# Parses and executes a block of Python code, and returns the eval result of the last statement
import ast
def exec_then_eval(code, _globals={}, _locals={}):
    block = ast.parse(code, mode='exec')
    # assumes last node is an expression
    last = ast.Expression(block.body.pop().value)
    extended_globals = {
        '__builtins__': {'isinstance': isinstance, 'print': print, 'int': int, 'float': float, 'bool': bool, 'str': str, 'tuple': tuple, 'len': len, 'set': set, 'dict': dict, 'eval': eval },
        **_globals,
    }
    exec(compile(block, '<string>', mode='exec'), extended_globals, _locals)
    return eval(compile(last, '<string>', mode='eval'), extended_globals, _locals)

def simply_exec(code, _globals={}, _locals={}):
    block = ast.parse(code, mode='exec')
    extended_globals = {
        '__builtins__': {'isinstance': isinstance, 'print': print, 'int': int, 'float': float, 'bool': bool, 'str': str, 'tuple': tuple, 'len': len, 'set': set, 'dict': dict, 'eval': eval },
        **_globals,
    }
    exec(compile(block, '<string>', mode='exec'), extended_globals, _locals)
