# Golf

- for enums, 0 indicates "no preference"
-

## Overview

**User**:

> may want to split some of this into a standalone "properties/preferences" table

- int - pk
- epochsec - created
- epochsec - updated
- char - password hash
- char - email
- char - name (display/prefix `@`)
- int - status (unverified, verified, inactive)
- char - gimmick (optional)
- int - age (range or explicit)
- geo - location (radius from address or zip code, for cities/towns use the "catalog" lat/lon)
- bool - lefty? (show as some sort of badge)
- float - handicap (bins)
- int - drinking? n/y/!
- int - ride/walk
- int - q:worst conditions you'll play in
- int - q:gimme distance
- int - q:play or practice, fun or serious
- int - q:ideal round time
- jsonb - preferences

- `create_user()`
- `get_user()`
- `update_user()`
- `delete_user()`
- `query_users()`
- `authenticate_user()`
- `get_user_preferences()`
- `set_user_preferences()`

**Event**:

- int - pk
- epochsec - created
- ~~epochsec - updated~~
- int - user_pk
- int - event
- jsonb - data

- `create_event()`
- `get_event()`
- ~~`update_event()`~~
- ~~`delete_event()`~~

**Courses**:

- location/address
- name
- parent organization
- num holes
- par
- hole breakdown
- notes/description
- contact info/website for booking(s)
- has_been_played

Microservices:

- User Service: core
- Event Service: core
- Course Service: core
- Alert Service: handle email password resets, announcements, etc.
- Message Service: allow players to chat
- Location Service: how far are we from different points of interest/locations
- Calendar Service: when can you play, view overlapping free times
- Timeline Service: Users can search/match with local players
- Impression Service: leave reviews for players, "fist bump" after round
- Weather Service: what is the expected forcast for certain times
- Insight Service: look at our data
- Admin Service: view pending edits, create courses, update users, issue password reset

---

## User Stories

- create new account
- login using new account
- verify new account: service boundary with alert service
- reset password: s.b. with alert service
- track when the user logs in
- keep time-series data about login attempts, succeed/fail, resets issued, etc.

---

- Create account, login, and verify account, reset password
- Create profile, upload images, answer some fun questions and customize preferences
- Search for users with profile filters such as distance radius, handicap
- View courses in the area and access website or view contact info
- Users can designate a course as "played" and have it show on their profile

## Spec

### Profile

- mini view: displayed in search results & swipe view
- full view: shown when a profile is selected for detailed viewing/interaction
- message button

### Message

- inbox with compose & search
- list view of each conversation
- conversation detail showing latest messages with infinite up scroll/pagination

### Conversation

- for each set of sender-receiver message pairs, we compile the series of messages into a "conversation"
- pagination is implemented, as well as notification tracking

```sql
-- returns all conversation tuple pairs;
-- for each pair, get latest as-is & with cols swapped, take most recent

-- returns 2 cols of row-tuples
SELECT t1.src_fk, t1.dst_fk
FROM messages t1
EXCEPT
SELECT t1.src_fk, t1.dst_fk
FROM messages t1
INNER JOIN messages t2
ON t1.src_fk = t2.dst_fk AND t1.dst_fk = t2.src_fk
AND t1.src_fk > t1.dst_fk;
```
