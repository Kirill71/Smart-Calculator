from enum import Enum, auto


class Priority:
    _priority = {'+': 1, '-': 1, '*': 2, '/': 2, '^': 3}

    def get_priority(self, operator):
        DEFAULT_PRIORITY = -1
        return self._priority.get(operator, DEFAULT_PRIORITY)

    def compare_priority(self, token1, token2):
        return self.get_priority(token1) <= self.get_priority(token2)


class Token:
    # TODO: Think about TokenVisitor and token hierarcy,
    #  because Token it's not SOLID class

    def __init__(self, token):
        self._token = token

    def is_sign_digit(self):
        unary_operations = ('+', '-')
        sign = self._token[0]
        number = self._token[1:]
        return sign in unary_operations and number.isdigit()

    def is_digit(self):
        return self._token.isdigit() or self.is_sign_digit()

    def is_variable(self):
        return self._token.isalpha()

    def is_alphanum(self):
        return not self.is_digit() and not self.is_variable() and self._token.isalpha()

    def is_operator(self):
        supported_operations = ('+', '-', '/', '*', '^')
        return self._token in supported_operations

    def is_left_bracket(self):
        LEFT_BRACKET = '('
        return self._token == LEFT_BRACKET

    def is_right_bracket(self):
        RIGHT_BRACKET = ')'
        return self._token == RIGHT_BRACKET

    def __str__(self):
        return self._token

    def __float__(self):
        return float(self._token)

    def __eq__(self, other):
        return self._token == str(other)

    def __hash__(self):
        return hash(self._token)


class ITokenizer:

    def __init__(self, expression):
        self._expression = expression


class AssignmentTokenizer(ITokenizer):

    def tokenize(self):
        return list(map(Token, list(map(str.strip, self._expression.replace('=', ' = ').split('=')))))


class ExpressionTokenizer(ITokenizer):
    unary_operations = ('+', '-')

    def _remove_signs(self):
        i = 0
        expr = list(self._expression)
        if expr in self.unary_operations and expr[1].isdigit():
            expr[0] += expr[1]
            expr.remove(expr[1])

        while i < len(expr):
            if expr[i] == '-' and expr[i + 1] == '-' or expr[i] == '+' and expr[i + 1] == '+':
                expr[i + 1] = '+'
                expr.remove(expr[i])
                i -= 1
            elif expr[i] == '+' and expr[i + 1] == '-' or expr[i] == '-' and expr[i + 1] == '+':
                expr[i + 1] = '-'
                expr.remove(expr[i])
                i -= 1
            i += 1

        return ''.join(expr)

    def tokenize(self):
        return list(map(Token, self._remove_signs().replace('(', '( ')
                        .replace(')', ' )')
                        .replace('+', ' + ')
                        .replace('-', ' - ')
                        .replace('*', ' * ')
                        .replace('/', ' / ')
                        .replace('^', ' ^ ')
                        .split()))


class Parser:
    def __init__(self, vars):
        self._vars = vars

    def convert_to_postfix_notation(self, expression):
        postfix_notation = []
        operations = []
        priority = Priority()
        tokenizer = ExpressionTokenizer(expression)
        tokens = tokenizer.tokenize()
        for token in tokens:
            if token.is_digit() or token in self._vars:
                postfix_notation.append(token)
            elif token.is_operator() or token.is_left_bracket():
                if len(operations) > 0:
                    if priority.compare_priority(token, operations[-1]) and not token.is_left_bracket():
                        postfix_notation.append(operations.pop())
                operations.append(token)
            elif token.is_right_bracket():
                while True:
                    operand = operations.pop()
                    if operand.is_left_bracket():
                        break
                    postfix_notation.append(operand)

        if any([operand for operand in operations if operand.is_left_bracket() or operand.is_right_bracket()]):
            raise ArithmeticError

        while len(operations) > 0:
            postfix_notation.append(operations.pop())

        return postfix_notation

    def parse(self, expression):
        process_stack = []
        postfix_notation = self.convert_to_postfix_notation(expression)
        for token in postfix_notation:
            if token.is_operator():
                op2 = process_stack.pop()
                op1 = process_stack.pop()
                if token == '+':
                    process_stack.append(op1 + op2)
                elif token == '-':
                    process_stack.append(op1 - op2)
                elif token == '*':
                    process_stack.append(op1 * op2)
                elif token == '/':
                    try:
                        process_stack.append(op1 / op2)
                    except ZeroDivisionError:
                        print('Division by zero!')
                elif token == '^':
                    process_stack.append(op1 ** op2)

            elif token in self._vars:
                process_stack.append(float(self._vars[token]))
            else:
                process_stack.append(float(token))

        if len(process_stack) > 1:
            raise ArithmeticError

        return int(process_stack.pop())


class EmptyCommandHandler:

    def __init__(self, handler):
        self._handler = handler

    def handle(self, request):

        if request == '':
            return True

        if self._handler is not None:
            return self._handler.handle(request)

        return False


class ExitCommandHandler(EmptyCommandHandler):

    def __init__(self):
        super().__init__(None)

    def handle(self, request):
        if request == '/exit':
            print('Bye!')
            return True

        return False


class HelpCommandHandler(EmptyCommandHandler):

    def handle(self, request):
        if request == '/help':
            print('The smart calculator')
            return True

        if super() is not None:
            return super().handle(request)

        return False


class UnknownCommandHandler(EmptyCommandHandler):

    def __init__(self):
        self._supported_command = ['/help', '/exit']
        super().__init__(None)

    def handle(self, request):
        if request.startswith('/') and request not in self._supported_command:
            print('Unknown command')
            return True

        if super() is not None:
            return super().handle(request)

        return False


class IValidationHandler:

    def __init__(self, handler):
        self._handler = handler


class InvalidAssignmentHandler(IValidationHandler):

    def __init__(self, handler, vars):
        super().__init__(handler)
        self._vars = vars

    def handle(self, tokens):

        if len(tokens) > 2 or not tokens[0].is_variable() or tokens[1].is_alphanum() or (
                tokens[1].is_variable() and tokens[1] not in self._vars):
            print('Invalid assignment')
            return True

        if self._handler is not None:
            return self._handler.handle(tokens)

        return False


class InvalidIdentifierHandler(IValidationHandler):

    def __init__(self):
        super().__init__(None)

    def handle(self, tokens):
        if len(tokens) > 2 or (tokens[0].is_digit() or tokens[0].is_alphanum() or tokens[1].is_alphanum()):
            print('Invalid identifier')
            return True

        if self._handler is not None:
            return self._handler.handle(tokens)

        return False


class Settings:

    def __init__(self):
        self._cmds = HelpCommandHandler(UnknownCommandHandler())
        self._ext = ExitCommandHandler()

    def get_commands(self):
        return self._cmds

    def get_exit_command(self):
        return self._ext


class Status(Enum):
    EXIT = auto,
    CONTINUE = auto


class Calculator:

    def __init__(self):
        self._settings = Settings()
        self._vars = {}
        self._parser = Parser(self._vars)
        self._validation = InvalidAssignmentHandler(InvalidIdentifierHandler(), self._vars)

    def _add_variable(self, name, value):
        # case if we have assignment like this: a = b, where b = 5
        if self._vars.get(value) is not None:
            self._vars[name] = self._vars[value]
        else:
            self._vars[name] = value

    def _is_unknown_variable(self, expression):
        variable = Token(expression.strip())
        if variable.is_variable():
            print(self._vars.get(variable, 'Unknown variable'))
            return True
        return False

    def calculate(self, expression):
        if self._settings.get_commands().handle(expression):
            return Status.CONTINUE
        if self._settings.get_exit_command().handle(expression):
            return Status.EXIT

        if '=' in expression:
            tokenizer = AssignmentTokenizer(expression)
            tokens = tokenizer.tokenize()
            if self._validation.handle(tokens):
                return Status.CONTINUE
            name = tokens[0]
            value = tokens[1]
            self._add_variable(name, value)
        else:
            if self._is_unknown_variable(expression):
                return Status.CONTINUE
            try:
                print(self._parser.parse(expression))
            except (IndexError, ArithmeticError):
                print('Invalid expression')


if __name__ == '__main__':
    calculator = Calculator()
    while True:
        expression = input()
        status = calculator.calculate(expression)
        if status == Status.EXIT:
            break
        # no matter mistake or success we have to repeat input, until the 'exit' command is received
        elif status == Status.CONTINUE:
            continue
