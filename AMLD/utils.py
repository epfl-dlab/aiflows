from IPython.core.magic import register_cell_magic

@register_cell_magic
def compile_and_writefile(line, cell):
    # Compile the code in the cell
    compiled_code = compile(cell, '<string>', 'exec')
    # Write the compiled code to a file
    with open(line, 'w') as f:
        f.write(cell)