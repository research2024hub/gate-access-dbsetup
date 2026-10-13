"""Resolve legacy guest user ownership without guessing between memberships."""
from collections import defaultdict
from sqlalchemy import text


def resolve_guest_owners(guests, holders, overrides=None):
    overrides = overrides or {}
    by_user = defaultdict(list)
    by_id = {}
    for holder in holders:
        by_user[holder['user_id']].append(holder)
        by_id[holder['id']] = holder
    mapping = {}
    seen = set()
    for guest in guests:
        guest_id, user_id, estate_id = guest['id'], guest['creator_id'], guest['estate_id']
        seen.add(guest_id)
        if user_id is None:
            if guest_id in overrides:
                raise ValueError(f'Guest {guest_id} has no source owner; an ownership override is not allowed.')
            mapping[guest_id] = None
            continue
        candidates = [h for h in by_user[user_id]
                      if estate_id is None or h['estate_id'] == estate_id]
        if guest_id in overrides:
            chosen = by_id.get(overrides[guest_id])
            # The legacy FK names users, but API writers also stored holder IDs.
            # Accept that interpretation only when explicitly confirmed in a map.
            direct_holder = (chosen is not None and chosen['id'] == user_id
                             and estate_id is not None and chosen['estate_id'] == estate_id)
            if chosen is None or (chosen not in candidates and not direct_holder):
                raise ValueError(f'Guest {guest_id}: override must reference a membership for its source user and estate, '
                                 'or the explicitly confirmed stored account-holder ID in the same estate.')
        elif len(candidates) == 1:
            chosen = candidates[0]
        else:
            raise ValueError(
                f'Guest {guest_id}: found {len(candidates)} matching account holders. '
                'Resolve missing memberships or supply --guest-owner-map for ambiguous ownership.'
            )
        mapping[guest_id] = chosen['id']
    if set(overrides) - seen:
        raise ValueError('Guest owner map contains unknown guest IDs.')
    return mapping


def check_source_relationships(connection, metadata, overrides=None):
    guests = metadata.tables['guests']
    targets = {fk.target_fullname for fk in guests.c.creator_id.foreign_keys}
    if targets != {'users.id'}:
        raise ValueError('Expected legacy guests.creator_id to reference users.id; refusing to reinterpret ownership.')
    duplicates = connection.execute(text('''
        SELECT report_id FROM report_status
        GROUP BY report_id HAVING COUNT(*) > 1 LIMIT 1
    ''')).first()
    if duplicates:
        raise ValueError(
            'Source report_status contains multiple rows for a report; '
            'reconcile them explicitly before transfer. No rows were removed.'
        )
    holders = list(connection.execute(text('''
        SELECT ah.id, ah.user_id, pi.estate_id
        FROM account_holders ah LEFT JOIN personal_info pi ON pi.id=ah.personal_info_id
    ''')).mappings())
    guest_rows = connection.execute(text('''
        SELECT g.id, g.creator_id, pi.estate_id
        FROM guests g LEFT JOIN personal_info pi ON pi.id=g.personal_info_id
        ORDER BY g.id
    ''')).mappings()
    # Include soft-deleted memberships: an old guest may belong to one of them.
    return resolve_guest_owners(guest_rows, holders, overrides)


def remap_guest(row, mapping):
    result = dict(row)
    result['creator_id'] = mapping[row['id']]
    return result
