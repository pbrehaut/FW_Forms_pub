from collections import defaultdict


def get_allowed_pairs_for_zone(zone_rules):
    """Convert zone rules into a set of allowed source-dest pairs per zone"""
    allowed_pairs = {}
    for zone, rules in zone_rules.items():
        if rules is None:
            allowed_pairs[zone] = set()  # No pairs allowed
        else:
            pairs = set()
            for rule in rules:
                for src in rule['src']:
                    for dst in rule['dst']:
                        pairs.add((src, dst))
            allowed_pairs[zone] = pairs
    return allowed_pairs


def check_and_split_groups(pairs, zone, allowed_pairs):
    """
    Check if grouping these pairs would create invalid combinations by checking
    all possible source-destination permutations
    Returns: (valid_pairs, pairs_to_move)
    """
    # Get all unique sources and destinations from the pairs
    sources = {pair[0] for pair in pairs}
    dests = {pair[1] for pair in pairs}

    # Generate all possible combinations
    all_possible_pairs = {(src, dst) for src in sources for dst in dests}

    # Check each possible combination against zone rules
    valid_pairs = set()
    pairs_to_move = set()
    pairs_to_check = pairs.union(all_possible_pairs)  # Check both original and potential new pairs

    for pair in pairs_to_check:
        src, dst = pair
        # Check if this pair belongs to a specific zone
        found_valid_zone = False
        for zone_name, zone_allowed in allowed_pairs.items():
            if (src, dst) in zone_allowed:
                if zone_name != zone:
                    # If any possible combination belongs to a different zone,
                    # we need to split the group
                    pairs_to_move.update({p for p in pairs if p[0] == src or p[1] == dst})
                    found_valid_zone = True
                    break

        if not found_valid_zone and pair in pairs:  # Only keep original pairs
            valid_pairs.add(pair)

    # Remove any pairs that were marked for moving from valid_pairs
    valid_pairs -= pairs_to_move

    return valid_pairs, pairs_to_move


def group_and_collapse(data, zone_rules):
    # Convert zone rules to allowed pairs
    allowed_pairs = get_allowed_pairs_for_zone(zone_rules)

    # First pass: group by zone and firewall
    zone_specific_pairs = defaultdict(lambda: defaultdict(set))

    for item in data:
        src, dst = item[0]
        zone = item[1]
        firewalls = item[2]
        specific_fw = item[3]

        zone_specific_pairs[zone][(specific_fw, tuple(firewalls))].add((str(src), str(dst)))

    # Second pass: validate and split groups
    final_zone_pairs = []

    for zone, fw_pairs in zone_specific_pairs.items():
        for fw_key, pairs in fw_pairs.items():
            valid_pairs, pairs_to_move = check_and_split_groups(pairs, zone, allowed_pairs)

            # Keep valid pairs in their current group
            if valid_pairs:
                final_zone_pairs.append((zone, fw_key, valid_pairs))

            # Move pairs to their correct zones
            if pairs_to_move:
                final_zone_pairs.extend([(zone, fw_key, p) for p in pairs_to_move])

    return final_zone_pairs