# Client

- [React-Bootstrap Docs](https://react-bootstrap.github.io/components/alerts/)
- [Feather Icon Library](https://feathericons.com/)

Views:

- QR Code
- Friend list
- Profile preview

---

Components:

- [x] Notifications
  - [x] Toast
- [x] Navigation
  - [x] Links
    - [x] Feed
    - [x] Inbox
  - [x] Brand
- [x] Feed
  - [x] Links
    - [ ] Account
    - [ ] Calendar
    - [ ] Network
    - [ ] Search
  - [x] Timeline
    - [ ] CardBox
- [ ] Account
  - [ ] My Profile
    - [ ] Edit
  - [ ] My Location
    - [ ] Edit
  - [ ] My Settings
    - [ ] Edit
- [x] Calendar
  - [ ] Availability
- [x] Search
  - [x] Query
    - [x] Distance
  - [ ] Results
    - [ ] CardBox
- [x] Inbox
  - [x] Preview
- [x] Chat
  - [x] Bubbles
  - [x] Input
- [x] Profile
  - [x] Image
  - [x] Name & @
  - [x] Summary
    - [ ] Preferences
    - [ ] Prompts
    - [ ] Calendar
  - [ ] Location

---

Interface

```js
props = {
  notify: (e) => alert(e),
};
```

---

1. ProfileModel column: `user_fk = db.Column(db.Integer(), db.ForeignKey("users.pk"), nullable=False)`

2. ProfileModel column: `user = relationship("UserModel", back_populates="profile")`

3. UserModel column: `profile = relationship("ProfileModel", back_populates="user_fk", uselist=False)`

4. UserSchema field: `profile = fields.Nested(ProfileSchema, many=False)`

---

# UI Workflows

- login/logout
- timeline
- ***

TODO:

- full profile card
- prompt q/a database (on hold, get profile working first)
- mini profile card for listitem
- calendar preview for profile card, handle default query behaviors like "do we only ever care about today to 7 days out"
- map preview

- location update workflow
- profile update workflow
- image update workflow
- account reset/validate workflow
  - is_validation_required
  - check_validation_status
  - handle link/token generation

MOBILITY
