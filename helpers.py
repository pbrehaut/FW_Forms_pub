def get_topology(result_list):
    extracted_values = set()

    for item in result_list:
        # Get the third element of each tuple (the string with format like '1:COR:FW1, flow 1')
        field_string = item[2]

        # Split by ':' and get the second element
        fields = field_string.split(':')
        if len(fields) >= 2:
            extracted_values.add(fields[1])

    if len(extracted_values) == 1:
        return extracted_values.pop()
    else:
        return None