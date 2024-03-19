from IPython.core.magic import register_cell_magic
from omegaconf import OmegaConf

@register_cell_magic
def compile_and_writefile(line, cell):
    # Compile the code in the cell
    compiled_code = compile(cell, '<string>', 'exec')
    # Write the compiled code to a file
    with open(line, 'w') as f:
        f.write(cell)
        
    
def dict_to_yaml(dictionary, output_file):
    """
    Convert a dictionary to YAML using OmegaConf and write to a file.

    :param dictionary: Dictionary to convert.
    :type dictionary: dict
    :param output_file: Path to the output YAML file.
    :type output_file: str
    """
    # Convert dictionary to OmegaConf config object
    config = OmegaConf.create(dictionary)

    # Write the config object to the output YAML file
    OmegaConf.save(config, output_file)