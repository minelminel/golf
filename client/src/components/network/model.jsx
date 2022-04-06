export const Model = {
  followers: {
    content: [
      { pk: 2, username: "bob" },
      { pk: 3, username: "carl" },
      { pk: 4, username: "doug" },
    ],
    metadata: {
      page: 0,
      pages: 0,
      size: 10,
      total: 10,
      links: {
        first: "",
        previous: "",
        self: "",
        next: "",
        last: "",
      },
    },
  },
  following: {
    content: [
      { pk: 2, username: "bob" },
      { pk: 3, username: "carl" },
    ],
    metadata: {
      page: 0,
      pages: 0,
      size: 10,
      total: 10,
      links: {
        first: "",
        previous: "",
        self: "",
        next: "",
        last: "",
      },
    },
  },
};
