const Model = {
  user: {
    username: "michael",
    last_login: 1648975160890,
  },
  image: {
    avatar: "/images/1",
  },
  profile: {
    alias: "Michael Lawrenson",
    bio: "ipsum lorem emus dee",
    handicap: 3.1,
    // official: true,
    transport: 1,
    drinking: 1,
    weather: 2,
  },
  location: {
    location: {
      coordinates: [72, 42],
      type: "Point",
    },
    distance: 14,
  },
  calendar: {
    content: [
      { date: "04-01-22", available: [] },
      { date: "04-02-22", available: [] },
      { date: "04-03-22", available: [1, 2] },
      { date: "04-04-22", available: [] },
      { date: "04-05-22", available: [3] },
      { date: "04-06-22", available: [1, 2, 3] },
      { date: "04-07-22", available: [1, 2, 3] },
    ],
    metadata: {
      page: 0,
      pages: 1,
      size: 100,
      total: 3,
    },
  },
  messages: {
    content: [],
    metadata: {
      page: 0,
      pages: 1,
      size: 100,
      total: 3,
    },
  },
};
