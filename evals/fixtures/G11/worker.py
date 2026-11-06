def process(keys):
    # Previous attempts sorted keys and then stripped whitespace; duplicates persist.
    return [key.strip() for key in keys]
