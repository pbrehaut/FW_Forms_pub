from collections import defaultdict, OrderedDict


def combine_tuple_fields(data):
    result = {}
    for key, tuples in data.items():
        combined = defaultdict(list)
        for tuple_item in tuples:
            for i, field in enumerate(tuple_item):
                if isinstance(field, list):
                    combined[i].extend(field)
                else:
                    combined[i].append(field)

        # Remove duplicates while preserving order
        for i in combined:
            combined[i] = list(OrderedDict.fromkeys(combined[i]))

        result[key] = tuple(combined[i] for i in range(len(tuples[0])))

    return result.items()