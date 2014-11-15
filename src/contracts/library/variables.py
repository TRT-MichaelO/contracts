import inspect

from ..interface import Contract, ContractNotRespected, RValue, describe_value
from ..syntax import (W, oneOf, FollowedBy, NotAny, Word, alphanums, S)


class BindVariable(Contract):

    def __init__(self, variable, allowed_types, where=None):
        assert isinstance(variable, str) and len(variable) == 1
        assert allowed_types, '%r' % allowed_types
        Contract.__init__(self, where)
        self.variable = variable
        self.allowed_types = allowed_types

    def check_contract(self, context, value):
        if self.variable in context:
            expected = context[self.variable]
            if not (expected == value):
                # TODO: add where it was bound
                error = (
                'Expected value for %r was: %s\n'
                '        instead I received: %s' %
                         (self.variable, describe_value(expected),
                         describe_value(value)))
                raise ContractNotRespected(contract=self, error=error,
                                           value=value, context=context)

        else:
            # bound variable
            if not isinstance(value, self.allowed_types):
                error = ('Variable %r can only bind to %r, not %r.' %
                         (self.variable, self.allowed_types,
                          value.__class__.__name__))
                raise ContractNotRespected(self, error, value, context)

            context[self.variable] = value

    def __str__(self):
        return self.variable

    def __repr__(self):
        # XXX: invalid if tuple
        return 'BindVariable(%r,%s)' % (self.variable,
                                        self.allowed_types.__name__)

    @staticmethod
    def parse_action(allowed_types):
        def parse(s, loc, tokens):
            where = W(s, loc)
            variable = tokens[0]
            assert len(variable) == 1, \
                    ('Wrong syntax, matched %r as variable in %r.'
                     % (variable, s))
            # print ('Matched %r as variable in %r.' % (variable, s))
            return BindVariable(variable, allowed_types, where=where)
        return parse


class VariableRef(RValue):
    def __init__(self, variable, where=None):
        assert isinstance(variable, str)
        self.where = where
        self.variable = variable

    def eval(self, context):  # @ReservedAssignment
        var = self.variable
        if not var in context:
            raise ValueError('Unknown variable %r.' % var)
        return context[var]

    def __repr__(self):
        return "VariableRef(%r)" % self.variable

    def __str__(self):
        return "%s" % self.variable

    @staticmethod
    def parse_action(s, loc, tokens):
        where = W(s, loc)
        return VariableRef(tokens[0], where=where)


class ScopedVariableRef(RValue):

    """
    A variable whose value is extracted by name from the scope where the spec is defined.
    """

    def __init__(self, value, where=None):
        self.where = where
        self.value = value

    def eval(self, context):
        return self.value

    def __repr__(self):
        return "ScopedVariableRef(%r)" % self.value

    def __str__(self):
        return str(self.value)

    @classmethod
    def _lookup_from_calling_scope(cls, token):
        """
        Extract the value of the token from the scope where the spec is defined
        """

        # We walk the callstack from the outside in, searching for the
        # frame where the spec is defined
        #
        # XXX Check if there are other places where a spec might be defined
        from .. import decorate, parse, check, fail

        frames = inspect.getouterframes(inspect.currentframe())
        frames = [f[0] for f in frames[::-1]]
        fcodes = [f.f_code for f in frames]

        def find_invokation(func):
            # return the first frame where func is called, or raise ValueError
            # find first frame inside function, step out 1
            return lambda: frames[fcodes.index(func.func_code) - 1]

        def find_decorate():
            # return the first frame where decorate is called, or raise ValueError

            # Brittle: We must to determine whether user calls decorate
            #          directly (in which case relevant scope is 1 frame out)
            #          or indirectly via @contract() (scope is 2 frames out)
            #          The implementation relies on the name `tmp_wrap` of the
            #          hidden function inside @contract.
            idx = fcodes.index(decorate.func_code)

            if frames[idx - 1].f_code.co_name == 'tmp_wrap':
                # decorate() called via @contract, Step out 2 frames
                return frames[idx - 2]

            # decorate() called oustide of @contract, step out 1 frame
            return frames[idx - 1]

        # search order important
        searchers = [find_decorate,
                     find_invokation(check),
                     find_invokation(fail),
                     find_invokation(parse)]
        for s in searchers:
            try:
                f = s()
            except (ValueError, IndexError):
                continue
            if not f:
                continue
            return eval(token, f.f_locals, f.f_globals)

        raise RuntimeError("Cound not find a scope to lookup %s" % token)

    @classmethod
    def parse_action(cls, s, loc, tokens):
        val = cls._lookup_from_calling_scope(tokens[0])
        where = W(s, loc)
        return cls(val, where=where)

alphabetu = 'A B C D E F G H I J K L M N O P Q R S T U W V X Y Z '
alphabetl = 'a b c d e f g h i j k l m n o p q r s t u w v x y z '

# Special case: allow an expression like AxBxC
nofollow = 'a b c d e f g h i j k l m n o p q r s t u w v   y z'
# also do not commit if part of word (SEn, a_2)
nofollow += 'A B C D E F G H I J K L M N O P Q R S T U W V X Y Z '
nofollow += '0 1 2 3 4 5 6 7 8 9 _'
# but recall 'axis_angle'
int_variables = (oneOf(alphabetu.split())
                  + FollowedBy(NotAny(oneOf(nofollow.split()))))
misc_variables = (oneOf(alphabetl.split())
                  + FollowedBy(NotAny(oneOf(nofollow.split() + ['x']))))
int_variables_ref = int_variables.copy().setParseAction(
                                                    VariableRef.parse_action)
misc_variables_ref = misc_variables.copy().setParseAction(
                                                    VariableRef.parse_action)

#int_variables = oneOf(alphabetu.split()) + FollowedBy(White() ^ 'x')

# These must be followed by whitespace; punctuation
#misc_variables = oneOf(alphabet.lower()) + FollowedBy(White()) 

nofollow = 'a b c d e f g h i j k l m n o p q r s t u w v   y z '
nofollow += ' * - + /'
nofollow += 'A B C D E F G H I J K L M N O P Q R S T U W V X Y Z '
nofollow += '0 1 2 3 4 5 6 7 8 9 _'
int_variables2 = (oneOf(alphabetu.split())
                  + FollowedBy(NotAny(oneOf(nofollow.split()))))
misc_variables2 = (oneOf(alphabetl.split())
                   + FollowedBy(NotAny(oneOf(nofollow.split() + ['x']))))
int_variables_contract = int_variables2.setParseAction(
                                                BindVariable.parse_action(int))
misc_variables_contract = misc_variables2.setParseAction(
                                            BindVariable.parse_action(object))


scoped_variables = (S('!') + Word(alphanums + '_'))
scoped_variables_ref = scoped_variables.setParseAction(ScopedVariableRef.parse_action)
