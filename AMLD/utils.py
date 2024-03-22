from IPython.core.magic import register_cell_magic
from omegaconf import OmegaConf
import os


@register_cell_magic
def compile_and_writefile(line, cell):
    # Compile the code in the cell
    compiled_code = compile(cell, '<string>', 'exec')
    #check if all directories exist and create them if they don't   
    # Extract the directory path from the file path
    directory = os.path.dirname(line)

    # Check if the directory exists
    if not os.path.exists(directory):
        # Create the directory if it doesn't exist
        os.makedirs(directory)
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
    
    directory = os.path.dirname(output_file)

    # Check if the directory exists
    if not os.path.exists(directory):
        # Create the directory if it doesn't exist
        os.makedirs(directory)

    #wirite file in yaml format
    with open(output_file, 'w') as f:
        OmegaConf.save(config, f.name)