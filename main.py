from core.element import Element
from core.manager import Manager
from core.context.bottom import BottomContext
from core.context.generic import GenericContext
from core.context import custom_contexts
from state.devstate import DevState
from bootstrap.simple_class_diagrams import bootstrap_scd

import inspect
from ast import literal_eval
import sys
import signal
signal.signal(signal.SIGINT, signal.default_int_handler)


def params(method):
    annotations = {
        "core.element.Element[str]": "String",
        "core.element.Element[int]": "Integer",
        "core.element.Element[float]": "Float",
        "core.element.Element[bool]": "Boolean"
    }
    sign = inspect.signature(method)
    for param in sign.parameters.values():
        param_type = annotations.get(str(param.annotation), "Element")
        if param.default is param.empty:
            yield param.name, param_type
        else:
            yield param.name, param_type, param.default


def input_args(method):
    args = []
    for param_tuple in params(method):
        if len(param_tuple) == 3:
            param_name, param_type, param_default = param_tuple
            arg = input(f"{param_type} {param_name} (default = {param_default.value})? ")
            if arg == '':
                arg = param_default.value
                arg = Element(value=arg)
                args.append(arg)
                continue
        else:
            param_name, param_type = param_tuple
            while True:
                arg = input(f"{param_type} {param_name}? ")
                if arg == '':
                    print("This arguments is non-optional, please provide a value.")
                else:
                    break
        if arg is None:
            arg = Element()
        elif param_type in {"Boolean", "Integer", "Float"}:
            arg = Element(value=literal_eval(arg))
        else:
            arg = Element(value=arg)
        args.append(arg)
    return args


def model_management_loop(manager: Manager):
    try:
        print("\nCurrently no model is loaded. Following model management operations are available:")
        for m in manager.exposed_methods():
            print(f"\t* {m.__name__}")
        while True:
            command = input("\nPlease enter a command: ")
            try:
                method = next(m for m in manager.exposed_methods() if m.__name__ == command)
                user_args = input_args(method)
                model = method(*user_args)
                if model is not None and not model.is_none():
                    metamodel = Element(id=manager.state.read_dict(model.id, "Metamodel"))
                    modelling_loop(manager, model, metamodel)
                    break
            except StopIteration:
                print("Invalid command, please try again.")
    except KeyboardInterrupt:
        print("\nBye!")
        sys.exit()


def modelling_loop(manager: Manager, model: Element, metamodel: Element):
    model_name = manager.state.read_value(model.id)
    metamodel_name = manager.state.read_value(metamodel.id)
    if metamodel.is_none():
        context = BottomContext(manager.state, model)
        print(f"No metamodel found. Model {model_name} has been loaded in context Bottom.")
    else:
        context = custom_contexts.get(metamodel_name, GenericContext)(manager.state, model, metamodel)
        print(type(context))
        print(f"Model {model_name} has been loaded in context {metamodel_name}.")
    print(f"To return to the model management interface press CTRL + C.")
    print(f"The following operations are available in this context:")
    for m in context.exposed_methods():
        print(f"\t* {m.__name__}")
    try:
        while True:
            command = input("\nPlease enter a command: ")
            try:
                method = next(m for m in context.exposed_methods() if m.__name__ == command)
                user_args = input_args(method)
                model = method(*user_args)
                if model is not None and not model.is_none():
                    metamodel = Element(id=manager.state.read_dict(model.id, "Metamodel"))
                    modelling_loop(manager, model, metamodel)
                    break
            except StopIteration:
                print("Invalid command, please try again.")
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    state = DevState()
    bootstrap_scd(state)

    man = Manager(state)
    print("Welcome to MV2!")
    while True:
        model_management_loop(man)



