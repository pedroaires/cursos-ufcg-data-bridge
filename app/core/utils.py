def rename_columns(data: dict, mappings: dict):
    """Renomeia as chaves de um dicionario."""
    for key in mappings.keys():
        if key in data:
            data[mappings[key]] = data.pop(key)
    return data

def remove_extra_keys(data: dict, mappings: dict):
    """Remove as chaves extras de um dicionario."""
    keys_to_keep = set(mappings.values())
    return {k: v for k, v in data.items() if k in keys_to_keep}

def generate_disciplina_id(curso, curriculo, disciplina):
    return f"{curso}-{curriculo}-{disciplina}"