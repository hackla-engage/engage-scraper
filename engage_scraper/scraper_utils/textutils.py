def check_last_word(string_data):
    last_word = string_data.split(" ")[-1]
    if len(last_word) == 1 and last_word.lower() not in ["i", "a"]:
        return False
    elif len(last_word) == 2 and last_word.lower() not in ["an", "or", "if", "it", "as", "to"]:
        return False
    return True