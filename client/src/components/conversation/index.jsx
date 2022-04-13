import React from "react";
import { v4 as uuidv4 } from "uuid";
import { Container, Row, Col, Button } from "react-bootstrap";
import { Send } from "react-feather";

// import { Model } from "./model";
import { API } from "../../constants";
import { formatTimeSince } from "../../utils";

const state = {
  user: {
    pk: 1,
    username: "alice",
  },
};

const SRC = 1;
const DST = 2;

const ChatBubble = (props) => {
  const { timestamp = true } = props;
  const ours = props.src_fk === state.user.pk;
  return (
    <Row className={`justify-content-${ours ? "end" : "start"}`}>
      {timestamp && (
        <div
          className="text-center text-muted"
          style={{
            fontSize: "small",
            marginBottom: "0.5rem",
          }}
        >
          {formatTimeSince(props.created_at)}
        </div>
      )}
      <Col className="col-8">
        {/* show an optional timestamp */}
        <p
          className="shadow"
          style={{
            background: `var(--${ours ? "bs-secondary" : "bs-primary"})`,
            borderRadius: "10px",
            padding: "10px",
            color: "white",
          }}
        >
          {props.body}
        </p>
      </Col>
    </Row>
  );
};

const Input = (props) => {
  const [input, setInput] = React.useState(``);

  const type = (e) => {
    setInput(e.target.value);
  };

  const send = (e) => {
    console.log(`Send: ${input}`);
    props.onSubmit(input);
    setInput(``);
  };

  return (
    <Row className="align-items-end mb-3">
      <Col>
        <input
          onChange={type}
          value={input}
          as="textarea"
          rows={2}
          placeholder="Start typing..."
          style={{
            padding: "5px",
            borderRadius: "8px",
            border: "1px solid gray",
            marginTop: "10px",
            width: "100%",
          }}
        />
      </Col>
      <Col xs={2} sm={2} md={2} lg={2} className="text-end">
        <Button
          disabled={input.length < 1}
          onClick={send}
          style={{
            borderRadius: "8px",
          }}
        >
          <Send size={20} />
        </Button>
      </Col>
    </Row>
  );
};

const Conversation = () => {
  const [props, setProps] = React.useState({
    content: [],
    context: {},
    metadata: {},
  });

  React.useEffect(() => {
    window.scrollTo(0, document.body.scrollHeight);
  }, [props]);

  React.useEffect(() => {
    loadChat(SRC, DST);
  }, []);

  const loadChat = (src, dst) => {
    console.log(`Loading chat with ${src} and ${dst}`);
    fetch(`${API}/conversations/${src}/${dst}`, {
      method: "GET",
    })
      .then((response) => response.json())
      .then((json) => {
        setProps(json.data);
      });
  };

  const sendChat = (src, dst, body) => {
    console.log(`Sending message from ${src} to ${dst}: ${body}`);
    fetch(`${API}/messages`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        src_fk: src,
        dst_fk: dst,
        body: body,
      }),
    })
      .then((response) => response.json())
      .then((json) => {
        loadChat(SRC, DST);
      });
  };

  const WelcomeMessage = () => {
    return (
      <div
        className="text-center text-muted"
        style={{
          fontSize: "small",
          marginBottom: "0.5rem",
        }}
      >
        Start of your conversation
      </div>
    );
  };

  // get latest message sent by each party and show a timestamp for context
  const includeTimestampsFor = [
    props.content.find((element) => element.dst_fk === state.user.pk)?.pk,
    props.content.find((element) => element.src_fk === state.user.pk)?.pk,
  ].filter((e) => e);

  return (
    <>
      <Container>
        {props.metadata.page === props.metadata.pages && <WelcomeMessage />}
        {[...props.content].reverse().map((prop, i, row) => (
          <ChatBubble
            key={uuidv4()}
            timestamp={includeTimestampsFor.includes(prop.pk)}
            {...prop}
          />
        ))}
        <Input onSubmit={(body) => sendChat(SRC, DST, body)} />
      </Container>
    </>
  );
};

export default Conversation;
