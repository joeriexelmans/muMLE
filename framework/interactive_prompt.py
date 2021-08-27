from framework.manager import Manager
from state.devstate import DevState
from PyInquirer import prompt, Separator
from pprint import pprint
import prompt_questions as questions
from inspect import signature
from uuid import UUID


def generate_context_question(ctx_type, services):
    choices = [
        s.__name__.replace('_', ' ') for s in services
    ]
    choices = sorted(choices)
    choices.append(Separator())
    choices.append("close context")
    ctx_question = [
        {
            'type': 'list',
            'name': 'op',
            'message': f'Currently in context {ctx_type.__name__}, which operation would you like to perform?',
            'choices': choices,
            'filter': lambda x: x.replace(' ', '_')
        }
    ]
    return ctx_question


def main():
    state = DevState()
    man = Manager(state)

    while True:
        if man.current_model is not None and man.current_context is None:
            answer = prompt(questions.MODEL_SELECTED)
            ctx = man
        elif man.current_model is not None and man.current_context is not None:
            qs = generate_context_question(type(man.current_context), man.get_services())
            answer = prompt(qs)
            if answer['op'] == 'close_context':
                man.close_context()
                continue
            else:
                ctx = man.current_context
        else:
            answer = prompt(questions.MODEL_MGMT)
            ctx = man

        if answer['op'] == 'exit':
            break
        else:
            method = getattr(ctx, answer['op'])
            args_questions = []
            types = {}
            for p in signature(method).parameters.values():
                types[p.name] = p.annotation  # can't use filter in question dict, doesn't work for some reason...
                if p.annotation == UUID:
                    args_questions.append({
                        'type': 'list',
                        'name': p.name,
                        'message': f'{p.name.replace("_", " ")}?',
                        'choices': list(man.get_models()),
                        'filter': lambda x: state.read_value(state.read_dict(state.read_root(), x))
                    })
                else:
                    args_questions.append({
                        'type': 'input',
                        'name': p.name,
                        'message': f'{p.name.replace("_", " ")}?',
                        'filter': lambda x: False if x.lower() == 'false' else x
                    })
            args = prompt(args_questions)
            args = {k: types[k](v) for k, v in args.items()}
            try:
                output = method(**args)
                if output is not None:
                    try:
                        if isinstance(output, str):
                            raise TypeError
                        output = list(output)
                        if len(output) > 0:
                            for o in sorted(output):
                                print(f"\u2022 {o}")
                    except TypeError:
                        print(f"\u2022 {output}")
            except RuntimeError as e:
                print(e)


if __name__ == '__main__':
    print("""Welcome to...
      __  ____      _____  
     |  \/  \ \    / /__ \ 
     | \  / |\ \  / /   ) |
     | |\/| | \ \/ /   / / 
     | |  | |  \  /   / /_ 
     |_|  |_|   \/   |____|
    """)
    main()
