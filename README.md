# Golf

![alt](./client/src/static/logo.png)

[LOGO](https://www.brandcrowd.com/maker/logo/golf-ball-33641?text=whose%20away&colorPalette=grayscale)

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
- int - user_fk
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

---

### Message Queue

```python
import pika

connection = pika.BlockingConnection(
    pika.ConnectionParameters(
        "localhost", 5672, "/", pika.PlainCredentials("rabbit", "rabbit")
    )
)
channel = connection.channel()
channel.exchange_declare(exchange="golf.exchange")
channel.queue_declare(queue="golf.queue")
channel.queue_bind(
    queue="golf.queue", exchange="golf.exchange", routing_key="golf.routing"
)
channel.basic_publish(
    exchange="golf.exchange", routing_key="golf.routing", body="Hello World!"
)


def consume(ch, method, properties, body):
    print(f"Received body: {body}")


channel.basic_consume(queue="golf.queue", on_message_callback=consume, auto_ack=True)
channel.start_consuming()
```

---

## UI Presentations

utils
hooks
const

component structure:

- index.jsx
- style.jsx
- logic.jsx
- props.jsx

components:

- profile header
- profile calendar tray
- profile location panel

todo:

- splash & call to action
- login/register
- edit profile
- view profile
  - stats popout
  - map popout
- conversation inbox
- conversation chat
- timeline
- availablity calendar

---

## Calendar

- morning (6-11)
- midday (11-4)
- twilight (4-9)

```bash
curl -s localhost:4000 | jq -r 'keys[]'
```

---

# Walkaway Notes

- make the landing page fancy, CTA funnel
- finish up account settings ui/workflows
- email service, password reset, verification
- inbox/chat acknowledge notifications
- referral backend workflow, callback from URL
- emoji calendar export/display
- public profile view (?)
- location based search & recommendations
- timeline card component
- "Challenge" workflow: present with prompt, dismissable modal with callback(s)
- hashids

NOW:

- from user profile view, implement "follow" & "chat" buttons
- zip code support for location
- city/state support for location

LATER:

- test docker compose, peek at helm chart
- integrate redis session cache for shared persistence between api workers
- load balance both app & api

---

https://testdriven.io/blog/flask-server-side-sessions/

---

- Flask factory
- Redis session backend
- Flask mail
- Async job queue
- Base Model
- Base Schema
- Identity Model
- Identity Schema
- Identiy Manager
- Identity Routes
- Unit Test

```yaml
/identity/register
/identity/login

/user/get/<key>
/user/edit/<key>
/user/query?params

/network/follow/<src>/<dst>
/network/unfollow/<src>/<dst>
/network/followers/<src>/<dst>
/network/following/<src>/<dst>
/network/is/follower/<src>/<dst>
/network/is/following/<src>/<dst>
/network/notifications/<key>
/network/notifications/ack/<key>

/message/send/<src>/<dst>
/message/inbox/<key>
/message/chat/<src>/<dst>
/message/notifications/<key>
/message/notifications/ack/<key>

/calendar/get/<key>/<date>
/calendar/edit/key/<date>
/calendar/query
# /feedback/send/<key>
# /feedback/get/<key>
# /feedback/query
# /feedback/notifications/<key>
# /feedback/notifications/ack/<key>
```

- 1.IdentityService

  - 1.1 Register User
  - 1.2 Login User
  - 1.3 Reset Password
  - 1.4 Verify Account

- 2. UserService

  - 2.1 Get Profile
  - 2.2 Edit Profile
  - 2.3 Search Users

- 3. NetworkService

  - 3.1 Friend User
  - 3.2 Unfriend User
  - 3.3 View Followers
  - 3.4 View Following
  - 3.5 Get Notification
  - 3.6 Mark Notification

- 4. MessageService

  - 4.1 Send Chat
  - 4.2 View Inbox
  - 4.3 View Conversation
  - 4.4 Get Notification
  - 4.5 Mark Notification

- 5. FeedbackService

  - 5.1 Give Feedback
  - 5.2 Receive Feedback
  - 5.3 Aggregate Feedback
  - 5.4 Get Notification
  - 5.5 Mark Notification

- 6. CalendarService

  - 6.1 View Calendar
  - 6.2 Update Calendar
  - 6.3 Search Overlap

- \*TimelineService

  - Recommendation Engine
  - Swipe Workflow

---

# Identity

```
{
    pk: primary key
    role: enum {user,admin}
    created_at: timestamp
    updated_at: timestamp
    last_login: timestamp
    username: string
    email: string
    password: hash
    verified: bool

    // relationships
    profile: {}
    messages: {}
    calendar: {}
    feedback: {}
    network: {}
}
```

- user registers by providing {username,email,password} and new entry is created (need to trigger creation of User record here ?)
- user receives authentication token upon successful login. this token populates a session with json-serializable models for permission & ownership checks
- manager exposes a route decorator which can inspect row-level permission challanges
- an email interface should be assumed to exist which may send messages for
  - verification upon signup
  - password reset link
  - general memos
- the system should track times of successful authentication
- the pk here should be used as primary key for adjacent tables
- schema should support 2 views
  - internal view for authentication/private access
  - public view for getting relationship views

```py
def im.exists(email: str, username: str) -> bool:
    identity = im.lookup(email, username)
    return bool(identity)

def im.lookup(pk: int, email: str, username: str) -> Identity:
    filters = {key: value for key, value in dict(email=email, username=username) if value}
    result = db.sesssion.query(Identity).filter_by(**filters)
    return result

def im.register(email: str, username: str, password: str) -> Token:
    if im.exists(email, username):
        return Conflict
    identity = IdentitySchema().load(**kwargs)
    identity.hash_password(identity.password)
    db.session.add(identity)
    db.session.commit()
    identity = IdentitySchema().dump(identity)
    um.create(identity)
    return identity

def im.login(email: Optional[str], username: Optional[str], password: str) -> Token:
    provided = IdentitySchema().load(email, username, password)
    identity = im.lookup(provided.email, provided.username):
    if not identity:
        return Unauthorized
    ok = identity.verify_password(provided.password)
    if not ok:
        return Unauthorized
    return im.grant(identity)


def im.grant(identity) -> Token:
    im.record_login(identity)
    token = jwt.serialize(identity, exp)
    return token

def im.email_verify_account(identity) -> bool:
    # generate verification link
    # send email async
    pass

def im.email_reset_password(identity) -> bool:
    # generate reset token link
    # send email async
    pass

def im.handle_verify_account(token, **kwargs):
    pass

def im.handle_reset_password(token, **kwargs):
    pass

def im._update_verified(pk, email) -> bool:
    identity = im.lookup(pk)
    identity.email = email
    db.session.commit()
    return True

def im._update_username(pk, username) -> bool:
    identity = im.lookup(pk)
    identity.username = username
    db.session.commit()
    return True

def im._update_email(pk, email) -> bool:
    identity = im.lookup(pk)
    identity.email = email
    db.session.commit()
    return True

def im._update_password(pk, password) -> bool:
    identity = im.lookup(pk)
    identity.hash_password(password)
    db.session.commit()
    return True

# 1.1 Register User
@app.route("/identity/register")
identity = im.register(email, username, password)
im.email_verify_account(identity)
token = im.login(email, username, password)
return token
# 1.2 Login User
@app.route("/identity/login")
identity = im.login(email, username, password)
if identity:
    token = im.grant(identity)
    session.update(token, identity)
return token
# 1.3 Reset Password
@app.route("/identity/reset/<token>")
im.email_reset_password(identity)
# 1.4 Verify Account
@app.route("/identity/verify/<token>")

```

# User

```
{
    pk: Identity.pk
    username: Identity.username

    profile_alias: string
    profile_bio: string

    image_data: blob
    image_base64: string
    img_href: string

    location_geometry: geojson
    location_label: string
    location_zip: string

    handicap: float
    mobility: integer
    drinking: integer
    weather: integer
}
```

- user has profile created for them upon registration
- user may edit portions of the profile including
  - name & bio
  - player traits
  - avitar upload
  - location
- user can search for other users either by username/alias or player traits & distance
- distance should be calculated and included in the serialized payloads (optionally) using the primary key as reference

```py
def um.lookup(pk) -> User:
    result = db.session.query(User).filter_by(pk=pk).first()
    return result

def um.create(identity) -> User:
    UserSchema().load(identity)

def um.read(pk) -> User:
    pass

def um.update(pk, **kwargs) -> User:
    pass

def um.delete(pk) -> bool:
    pass

def um.query(**kwargs) -> List[User]:
    pass

```

# Network

```
{
    pk: primary key
    created_at: timestamp
    updated_at: timestamp
    src_fk: Identity.pk
    dst_fk: Identity.pk
    ack: bool (notification acknowledgement)

    // relationships
    src: {User}
    dst: {User}
}
```

- User connects with another user in a mutually-exclusive manner, where the other user may or may not follow them reciprocally
- User can view their own followers & following connections
- User may remove an existing connection where they are the `src`
- Statistics about follower & following counts should be available natively or reliably within the pagination metadata
- Notifications should return data including total count
- Notifications should be ack'd using onClick callbacks, backed by redis store
- Acknowledgement url should be included in the payload data

```py

def nm.follow() -> bool:
    pass

def nm.unfollow() -> bool:
    pass

def nm.followers() -> List[User]:
    pass

def nm.following() -> List[User]:
    pass

def nm.is_follower() -> bool:
    pass

def nm.is_following() -> bool:
    pass

def nm.query() -> List[User]:
    pass

def nm.notifications() -> List[Notification]:
    pass

def nm.acknowledge() -> bool:
    pass

```

# Message

```
{
    pk: primary key
    created_at: timestamp
    updated_at: timestamp
    chat: ? do we have a quick way to lookup messages with perspective
    src_fk: Identity.pk
    dst_fk: Identity.pk
    ack: bool (notification acknowledgement)
    body: text

    // relationships
    src: {User}
    dst: {User}
}
```

- All messages come in the context of a conversation. If a message is sent and no prior chat history exists, a new chat should be registered using the `src` and `dst` primary keys
- Inbox view where for each existing registered chat, the most recent message is returned along with a `me` bool prop using session as reference
- Chat should return paginated data with most recent data first. This is more logical but will require a reverse in the client code
- If a chat is queried and no chat exists, a default view with both user contexts should be returned for display purposes
- Notifications should return data on a group-by basis such that the number returned is the total chats with unread messages
- Notifications should be ack'd using onClick callbacks, backed by redis store
- Acknowledgement url should be included in the payload data

```py
def mm.send() -> bool:
    pass

def mm.inbox() -> List[Message]:
    pass

def mm.chat() -> List[Message]:
    pass

def mm.notifications() -> List[Notification]:
    pass

def mm.acknowledge() -> bool:
    pass

```

# Feedback

```
{
    pk: primary key
    created_at: timestamp
    updated: timestamp
    src_fk: Identity.pk
    dst_fk: Identity.pk
    body: ? totally arbitrary at this point, just a placeholder for the entry itself

    // relationships
    src: {User}
    dst: {User}
}
```

- User can give feedback to another user 1x every 12 hours
- Eventually this could give way to a rating system but for now it's just a fist-bump type interaction
- Notifications et. al

```py

def fm.send() -> bool:
    pass

def fm.inbox() -> List[Message]:
    pass

def fm.chat() -> List[Message]:
    pass

def fm.notifications() -> List[Notification]:
    pass

def fm.acknowledge() -> List[Notification]:
    pass

```

# Calendar

```
create
{
    pk: primary key
    src_fk: Identity.pk
    date: Date
    time: integer (enum{morning,midday,twilight})

    // relationships
    src: {User}
}

view
{
    pk:
    src_fk:
    date: Date
    times: [...entries]

    // relationships
    src: {User}
}
```

- When the model is returned, the date should be included for all queried windows with an empty content list if no entries exist
- Querying should be heavily modified to account for the required group-by date behavior
- If an identity entry is to be created, just politely ignore it and return the existing entry
- Querying should support 2 use cases:
  - user
  - scheduler

```py

def cm.create() -> bool:
    pass

def cm.read() -> Calendar:
    pass

def cm.delete() -> bool:
    pass

def cm.query() -> List[Calendar]:
    pass

```

---

(1.1) The user registers an account and is logged in. An email is sent to their account containing a verification link, required for password reset. Upon logging in, they are presented with a series of cards for editing their profiles, in order: name & bio, attributes, location, image. These should be skippable and recallable (reuse for update workflow). Once some information is known about the user, suggest some connections for their network. Take them to their profile and show how the calendar works. A help screen should be easily accessible with miniatures of the basic workflows.

(2.1) The first branch from here is a user immediately wanting to find a partner. The search should consider players in an area of set size with optional minimum criteria. The most important things here are that distance is reasonable and there is calendar overlap. Perhaps an "RTG" mode that always returns a match on this query? The habit of updating the schedule needs to be super fluid, so populating a timeline card with the suggestion to set the next N day's availability will be critical. Perhaps optional filtering on "my network"? Anyway, so the user is returned a set of results from which they may inspect and visit profiles of. Messaging and following can be done directly from a profile. They chat with the user and establish a meeting. After the round, the users can easily "handshake" the other using a QR code, with stats populated in the user's profile.

(2.2) The second branch is that a user may spend some time on the app before planning an outing. They may wish to edit their profiles multiple times, search for other users regardless of scheduling, follow & chat with these users. They rely on much more organic discussion to set up a meeting.

(3.1) In either case, as a user maintains their account, their network & feedback begin to grow. They can display their profiles in a way they want to screenshot. Notifications regarding activity (chat, feedback, network) are visible driving a scoring mentality. The timeline shows regularly updated content regarding people near them who have connected, new users with similar traits, and friends who have upcoming availabilities. These cards are all set up in such a way that clicking the card allows the suggested action to happen automatically.

(4.1) The user logs in at a later time and has forgotten their login information. They click the "reset password" link but their account has not been verified yet. They can re-send a verification link or click an existing link in an email to verify. Once they are verified, the password reset link is mailed to them, which they click and are allowed to reset their password. They are then logged into their account.

(5.1) Identity-level information such as username/email/password can be changed via the Account Settings. There should be a "danger zone" section with a "delete account" button that simply marks the user as deactivated.

The fine print: email messages should be sent via an async task queue, with logic for retries. Session data needs to be consistent between instances, so Redis is a good choice here. Some thought into the pros/cons of notification systems as active "push" operations or passive query/update procedures is necessary.

"Should notification status be linked to the database record, or should notifications be actively pushed and consumed from something like a message broker?"

- Simple vs. Bulk operations
- Make microservice requests async
- Create "owner" column on all tables, requiring that value via the user session to `crud`. Optionally, some pages (user profiles) should be visible even be non-authenticated users, for the purposes of conversions.

---

Consensus on notifications: if anything, the notification system might be the most fun to implement. It should be entirely decoupled from the api call of pushing a message. Messages and things in general would keep a column "published" which is marked as such once it is picked-up by the notifier. We can query the notifications by user & channel, as well as optionally doing a group-by for the other user, so that multiple messages in a chat show as 1 bubble, similarly with feedback, etc.

The notifications can be optionally passed to a small variety of components which would indicate either a number of, or presence of notifications. By decoupling these, we can always show messages & activity even if the notification server is unavailable. Additionally, multiple modules can all leverage the same notification service to separate concerns within individual modules.

---

message is sent by user to a recipient. the message is posted to an api where the message manager creates a database record and emits an event. this event is handled by optionally multiple handers, here being notification publish & websocket heartbeat. notifications published to notif manager and are queried by other user(s) for changes. these query result notifs are passed to various components
