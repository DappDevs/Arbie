import vyper


# Compile the token
with open('Token.vy', 'r') as f:
    interface = vyper.compile_code(
            f.read(),
            output_formats=['abi', 'bytecode', 'bytecode_runtime'],
        )
