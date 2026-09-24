def minMeetingRooms(intervals):
    # At equal times: endings free their rooms first, then zero-length
    # meetings briefly take a room, then new meetings start.
    END, INSTANT, START = 0, 1, 2
    events = []
    for s, e in intervals:
        if s == e:
            events.append((s, INSTANT))
        else:
            events.append((s, START))
            events.append((e, END))
    events.sort()
    rooms = max_rooms = 0
    for _, kind in events:
        if kind == END:
            rooms -= 1
        elif kind == INSTANT:
            max_rooms = max(max_rooms, rooms + 1)
        else:
            rooms += 1
            max_rooms = max(max_rooms, rooms)
    return max_rooms

