from pyparsing import Optional, Suppress
from ..syntax import add_contract
from ..interface import Contract, ContractNotRespected
from ..syntax import W, contract, integer
from .dummy import DummyContract

class List(Contract):
    
    def __init__(self, where, length_contract=None, elements_contract=None):
        Contract.__init__(self, where)
        self.length_contract = length_contract
        self.elements_contract = elements_contract
    
    def check_contract(self, context, value): 
        if not isinstance(value, list):
            error = 'Expected a list, got %r.' % value.__class__.__name__
            raise ContractNotRespected(contract=self, error=error,
                                       value=value, context=context)
       
        if self.length_contract is not None:
            self.length_contract.check_contract(context, len(value))
        
        if self.elements_contract is not None:
            for i, element in enumerate(value):
                context2 = context.copy()
                self.elements_contract.check_contract(context2, element)
    
    def __repr__(self):
        s = 'list'
        if self.length_contract is not None:
            s += '[%r]' % self.length_contract
        if self.elements_contract is not None:
            s += '(%r)' % self.elements_contract
        return s
            
    @staticmethod
    def parse_action(s, loc, tokens):
        from .values import CheckOrder

        
        where = W(s, loc)
        
        if 'length_contract' in tokens:
            assert not 'length' in tokens
            length_contract = tokens['length_contract']
        elif 'length' in tokens:
            assert not 'length_contract' in tokens
            expected = tokens['length']
            length_contract = CheckOrder(where, None, expected, False, True, False)
        else:
            length_contract = None
            
        if 'elements_contract' in tokens:
            elements_contract = tokens['elements_contract']
        else: 
            elements_contract = None
        
        return  List(where,
                     length_contract=length_contract,
                     elements_contract=elements_contract)


O = Optional
S = Suppress

list_contract = (S('list') + 
                 # allow shortcut: list[1] instead of list[=1]
                 O(S('[') + (integer('length') ^ contract('length_contract')) + S(']')) + 
                 O(S('(') + contract('elements_contract') + S(')')))
list_contract.setParseAction(List.parse_action)


add_contract(list_contract)
