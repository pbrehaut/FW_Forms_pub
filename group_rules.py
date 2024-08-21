from collections import defaultdict


def group_and_concat_gateways(data):
    grouped_data = {}

    for item in data:
        key = item[:6]  # The first five fields are used as the key
        if key in grouped_data:
            grouped_data[key] += "\n" + item[6]  # Concatenate the seventh field
        else:
            grouped_data[key] = item[6]  # Initialize with the seventh field

    # Convert the grouped data back to a list of tuples
    result = [(key[0], key[1], key[2], key[3], key[4], key[5], grouped_data[key]) for key in grouped_data]

    return result


def group_and_collapse(data):
    # Initial grouping and collapsing
    initial_result = defaultdict(list)

    for item in data:
        key = (item[1], tuple(item[2]), item[3])  # Remove sorting here
        initial_result[key].append(item[0])

    # Collapsing and regrouping
    final_result = defaultdict(lambda: defaultdict(list))

    for (second, third, fourth), group in initial_result.items():
        first_elements = set(elem[0] for elem in group)
        second_elements = set(elem[1] for elem in group)

        # collapsed_first = '\n'.join(sorted(str(x) for x in first_elements))
        # collapsed_second = '\n'.join(sorted(str(x) for x in second_elements))

        collapsed_first = [str(x) for x in first_elements]
        collapsed_second = [str(x) for x in second_elements]

        # Regroup based on first and third entries of the key
        main_key = (second, fourth)
        sub_key = tuple(third)  # Remove sorting here

        final_result[main_key][sub_key] = (collapsed_first, collapsed_second, second, set(third), fourth)

    return dict(final_result)