from InquirerPy.separator import Separator

MODEL_SELECTED = [
    {
        'type': 'list',
        'name': 'op',
        'message': 'Model selected... Which operation would you like to perform?',
        'choices': [
            'get types',
            'select context',
            Separator(),
            'close model'
        ],
        'filter': lambda x: x.replace(' ', '_')
    }
]

MODEL_MGMT = [
    {
        'type': 'list',
        'name': 'op',
        'message': 'Which model management operation would you like to perform?',
        'choices': [
            'get models',
            'select model',
            'instantiate model',
            'check conformance',
            Separator(),
            'load state',
            'dump state',
            'to graphviz',
            Separator(),
            'exit'
        ],
        'filter': lambda x: x.replace(' ', '_')
    }
]
