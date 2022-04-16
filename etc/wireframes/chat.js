const Model = {
  conversations: {
    content: [
      {
        pk: 1,
        created_at: 1648975164281,
        src_fk: 1,
        dst_fk: 2,
        body: "hello world",
        read: false,
      },
      {
        pk: 4,
        created_at: 1648975160890,
        src_fk: 3,
        dst_fk: 1,
        body: "ipsum lorem",
        read: true,
      },
    ],
    metadata: {
      page: 0,
      pages: 1,
      size: 100,
      total: 2,
    },
  },
};
