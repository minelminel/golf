-- reset
-- DROP TYPE IF EXISTS "status";
-- DROP TYPE IF EXISTS "drinking";
-- DROP TYPE IF EXISTS "pace";
-- DROP TYPE IF EXISTS "weather";
-- DROP TYPE IF EXISTS "gimme";
-- DROP TYPE IF EXISTS "transport";

DROP TABLE IF EXISTS "users" CASCADE;
DROP TABLE IF EXISTS "profiles" CASCADE;

-- create
-- CREATE TYPE "status" AS ENUM (
--   'unset',
--   'active',
--   'inactive'
-- );

-- CREATE TYPE "drinking" AS ENUM (
--   'unset',
--   'none',
--   'some',
--   'lots'
-- );

-- CREATE TYPE "pace" AS ENUM (
--   'unset',
--   'fast',
--   'average',
--   'slow'
-- );

-- CREATE TYPE "weather" AS ENUM (
--   'unset',
--   'anything',
--   'average',
--   'perfect'
-- );

-- CREATE TYPE "gimme" AS ENUM (
--   'unset',
--   'polite',
--   'friendly',
--   'never'
-- );

-- CREATE TYPE "transport" AS ENUM (
--   'unset',
--   'walk',
--   'ride'
-- );

CREATE TABLE "users" (
  "pk" SERIAL PRIMARY KEY,
  "created_at" bigint,
  "updated_at" bigint,
  "visited_at" bigint,

  "verified" boolean DEFAULT (false),
  "email" varchar NOT NULL UNIQUE,
  "username" varchar NOT NULL UNIQUE,
  "password" varchar NOT NULL
);

CREATE TABLE "profiles" (
  "pk" SERIAL PRIMARY KEY,
  "fk" int, --  FOREIGN KEY REFERENCES users(pk),
  "created_at" bigint,
  "updated_at" bigint,
  "visited_at" bigint,

  "fullname" varchar NOT NULL,
  "bio" text,
  "age" int,
  "handicap" float,
  "location" varchar,
  "drinking" int,
  "pace" int,
  "weather" int,
  "gimme" int,
  "transport" int
);

-- CREATE TABLE "connections" (
--   "pk" SERIAL PRIMARY KEY,
--   "fk" int,
--   -- "created_at" bigint DEFAULT (SELECT ( ROUND ( EXTRACT(epoch FROM now())))),
--   "created_at" bigint,
--   "updated_at" bigint,
--   "friend" int
-- );

ALTER TABLE "profiles" ADD FOREIGN KEY ("fk") REFERENCES "users" ("pk");

-- ALTER TABLE "Users" ADD FOREIGN KEY ("pk") REFERENCES "Connections" ("fk");
