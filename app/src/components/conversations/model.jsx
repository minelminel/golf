export const Model = {
  content: [
    {
      pk: 3,
      created_at: Date.now() - 1000 * 60 * 0.5,
      src_fk: 4,
      src: {
        pk: 4,
        username: "dylan",
      },
      dst_fk: 1,
      dst: {
        pk: 1,
        username: "alice",
      },
      body: "hey alice, what's up",
      read: false,
    },
    {
      pk: 2,
      created_at: Date.now() - 1000 * 60 * 6,
      src_fk: 1,
      src: {
        pk: 1,
        username: "alice",
      },
      dst_fk: 2,
      dst: {
        pk: 2,
        username: "bob",
      },
      body: "hello world!",
      read: true,
    },
    {
      pk: 1,
      created_at: Date.now() - 1000 * 60 * 60 * 7,
      src_fk: 3,
      src: {
        pk: 3,
        username: "carl",
      },
      dst_fk: 1,
      dst: {
        pk: 1,
        username: "alice",
      },
      body: "longer messages should be truncated with ellipses",
      read: false,
    },
  ],
  metadata: {
    checksum: "f572d396fae9206628714fb2ce00f72e94f2258f",
    page: 0,
    pages: 1,
    size: 25,
    total: 2,
  },
};
