def rename_columns(data: dict, mappings: dict):
    """Rename columns in a dictionary."""
    for key in mappings.keys():
        if key in data:
            data[mappings[key]] = data.pop(key)
    return data

def remove_extra_keys(data: dict, mappings: dict):
    """Remove extra keys from a dictionary."""
    keys_to_keep = set(mappings.values())
    return {k: v for k, v in data.items() if k in keys_to_keep}

def generate_disciplina_id(curso, curriculo, disciplina):
    return f"{curso}-{curriculo}-{disciplina}"