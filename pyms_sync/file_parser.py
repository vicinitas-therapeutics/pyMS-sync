import re

def parse_file_name(file_name):
    """
    Parse the file name and extract components.
    :param file_name: str - The file name to parse
    :return: dict - A dictionary with the extracted components
    """
    pattern = r'(?P<ExperimentID>[^_]+)_(?P<Instrument>[^_]+)_(?P<Method>[^_]+)_(?P<Protein>[^_]+)_(?P<Condition>[^_]+)_(?P<Concentration>[^_]+)_(?P<Time>[^_]+)_(?P<BioReplicate>[^_]+)_(?P<TechnicalRep>[^_]+)'
    match = re.match(pattern, file_name)
    if match:
        return match.groupdict()
    else:
        raise ValueError("File name does not match the expected pattern")

