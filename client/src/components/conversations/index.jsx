import React from "react";
import { v4 as uuidv4 } from "uuid";

import { ListGroup, Badge } from "react-bootstrap";
import { Model } from "./model";

import { formatTimeSince } from "../../utils";

const state = {
  user: {
    pk: 1,
    username: "alice",
  },
};

const Message = (props) => {
  const ours = props.src_fk === state.user.pk;
  return (
    <ListGroup.Item
      as="li"
      className="d-flex mt-3 shadow"
      style={{
        borderRadius: "15px",
        paddingTop: "15px",
        paddingBottom: "15px",
      }}
    >
      <div className="frame ms-2">
        <img
          alt={`${ours ? props.dst.username : props.src.username}`}
          title={`/images/${ours ? props.dst.username : props.src.username}`}
          src="http://192.168.1.114:4000/images/1"
          className="cropped"
          style={{
            width: "36px",
            height: "36px",
          }}
        />
      </div>
      <div className="ms-3 me-auto">
        <div className="fw-bold">
          @{ours ? props.dst.username : props.src.username}
          &nbsp;
          {ours && !props.read ? (
            <Badge
              pill
              bg="primary"
              style={{
                fontSize: "x-small",
              }}
            >
              &nbsp;
            </Badge>
          ) : null}
        </div>
        {/* TODO: FIXME ellipsis */}
        <div>
          {ours ? `You: ` : ``}
          {props.body.length > 30
            ? props.body.slice(0, 30) + "..."
            : props.body}
        </div>
      </div>
      <div
        className="text-muted float-right"
        style={{
          fontSize: "small",
          fontWeight: "bold",
          marginTop: "auto",
          marginBottom: "auto",
        }}
      >
        {formatTimeSince(props.created_at)}
      </div>
    </ListGroup.Item>
  );
};

const Conversations = () => {
  const props = Model;
  return (
    <>
      {props.content.map((prop) => (
        <Message key={uuidv4()} {...prop} />
      ))}
    </>
  );
};

export default Conversations;
