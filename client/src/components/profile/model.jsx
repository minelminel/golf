export const Model = {
  profile: {
    handicap: 3.1,
    ridewalk: 1,
    drinking: 1,
    weather: 2,
    prompts: [
      {
        q: "question 1",
        a: "some user provided answer to 1",
      },
      {
        q: "question 2",
        a: "an answer given for 2",
      },
      {
        q: "question 3",
        a: "my response to the third prompt",
      },
    ],
  },
  calendar: {
    content: [
      { date: "04/01/22", available: [] },
      { date: "04/02/22", available: [] },
      { date: "04/03/22", available: [1, 2] },
      { date: "04/04/22", available: [] },
      { date: "04/05/22", available: [3] },
      { date: "04/06/22", available: [1, 2, 3] },
      { date: "04/07/22", available: [1, 2, 3] },
    ],
    metadata: {
      page: 0,
      pages: 1,
      size: 100,
      total: 3,
    },
  },
};
