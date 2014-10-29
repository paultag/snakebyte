#!/usr/bin/env python3
import sys
import types
import opcode

if sys.version_info <= (2, 8, 0):
    raise Exception("3.x only")

omap = opcode.opmap


class Compiler:
    def __init__(self):
        self.co_consts = []
        self.co_freevars = []
        self.co_kwonlyargcount =[]
        self.co_lnotab = []
        self.co_names = []
        self.co_varnames = []
        self.co_code = []

        self.jumps = {}
        self.labels = {}

        self.names = {}
        self.vars = {}
        self.consts = {}

    def _octet_int(self, index):
        return ((index & 0xFF), ((index >> 8) & 0xFF))

    def _set_jump(self, location, where):
        index = self.labels[where]
        low, high = self._octet_int(index)
        self.co_code[location] = low
        self.co_code[location + 1] = high

    #       GENERIC OPCODE HANDLERS

    def compile_single(self, opcode):
        self.co_code.append(omap[opcode])

    def compile_multi(self, opcode, args):
        index = int(args)
        self.co_code.append(omap[opcode])
        h, l = self._octet_int(index)
        self.co_code.append(h)
        self.co_code.append(l)

    def compile_jump(self, opcode, label):
        where = len(self.co_code) + 1
        self.jumps[where] = label
        return self.compile_multi(opcode, 0)

    def compile_name_arg(self, opcode, name):
        name = self.names[name]
        return self.compile_multi(opcode, name)

    def compile_const_arg(self, opcode, name):
        name = self.consts[name]
        return self.compile_multi(opcode, name)

    def compile_var_arg(self, opcode, name):
        name = self.vars[name]
        return self.compile_multi(opcode, name)

    #       ASM OPTIONS

    def compile_DEF_LABEL(self, _, name):
        self.labels[name] = len(self.co_code)

    def compile_DEF_NAME(self, _, name):
        name = name.strip()
        index = len(self.co_names)
        self.co_names.append(name)
        self.names[name] = index

    def compile_DEF_VAR(self, _, name):
        name = name.strip()
        index = len(self.co_varnames)
        self.co_varnames.append(name)
        self.vars[name] = index

    def compile_DEF_CONST(self, _, args):
        name, const = [x.strip() for x in args.split(" ", 1)]
        const = eval(const)
        index = len(self.co_consts)
        self.co_consts.append(const)
        self.consts[name] = index

    def compile_RAW(self, _, args):
        try:
            stream = eval(args)
        except SyntaxError as e:
            print(args)
            raise

        for x in stream:
            self.co_code.append(x)

    #       ENABLED BYTECODE

    compile_LOAD_GLOBAL = compile_name_arg
    compile_LOAD_CONST = compile_const_arg
    compile_LOAD_FAST = compile_var_arg
    compile_LOAD_ATTR = compile_name_arg
    compile_IMPORT_NAME = compile_name_arg
    compile_IMPORT_FROM = compile_name_arg
    compile_STORE_FAST = compile_var_arg

    def compile_COMPARE_OP(self, instruction, args):
        op = args.strip()
        self.compile_multi(instruction, opcode.cmp_op.index(op))

    #       COMPILER

    def compile(self, instruction, args):
        try:
            fn = getattr(self, "compile_{}".format(instruction))
        except AttributeError:
            i_id = omap[instruction]
            if i_id in opcode.hasjabs:
                fn = self.compile_jump
            elif i_id > opcode.HAVE_ARGUMENT:
                fn = self.compile_multi
            else:
                fn = self.compile_single
        if args:
            return fn(instruction, args)
        return fn(instruction)

    def build(self):
        for location, where in self.jumps.items():
            self._set_jump(location, where)

        return types.CodeType(
            0, 0, 0, 3, 0,
            bytes(self.co_code),
            tuple(self.co_consts),
            tuple(self.co_names),
            tuple(self.co_varnames),
            "hi", "hi", 0, b"",
        )


class Snakebyte:
    def __init__(self, path):
        self.path = path

    def parse(self):
        in_header = True
        with open(self.path, 'r') as fd:
            for line in (x.strip() for x in fd.readlines()):
                if line == "" or line.startswith(";"):
                    continue
                if " " in line:
                    instruction, arg = line.split(None, 1)
                    yield (instruction, arg)
                else:
                    yield (line, None)

    def debug(self):
        compiler = Compiler()
        for (instruction, args) in self.parse():
            print(instruction, args)
            compiler.compile(instruction, args)
        code = compiler.build()
        import dis
        dis.dis(code)

    def compile(self):
        compiler = Compiler()
        for (instruction, args) in self.parse():
            compiler.compile(instruction, args)
        return compiler.build()


def main(fpath, *args):
    afk = Snakebyte(fpath)
    x = afk.compile()
    import marshal

    if "write" in args:
        where = args[-1]
        with open(where, 'wb') as fd:
            marshal.dump(x, fd)
        return

    if "dry" in args:
        return afk.debug()

    try:
        exec(x, {}, globals())
    except Exception:
        import dis
        dis.dis(x)
        raise

if __name__ == "__main__":
    import sys
    main(*sys.argv[1:])
