import React from "react";
import {
  Container,
  ButtonGroup,
  Button,
  Row,
  Col,
  ListGroup,
} from "react-bootstrap";
import { v4 as uuidv4 } from "uuid";

import { Model } from "./model";

const Network = (props) => {
  const [tab, setTab] = React.useState(`followers`); // followers
  // const props = { ...Model };
  return (
    <>
      <Container>
        <Row>
          <Col>
            <ButtonGroup className="d-flex">
              <Button
                className="shadow"
                onClick={() => setTab("followers")}
                variant={`${tab === "followers" ? "" : "outline-"}secondary`}
              >
                Followers
              </Button>
              <Button
                className="shadow"
                onClick={() => setTab("following")}
                variant={`${tab === "following" ? "" : "outline-"}secondary`}
              >
                Following
              </Button>
            </ButtonGroup>
          </Col>
        </Row>
        <Row>
          <Col>
            <ListGroup className="mt-3" variant="flush">
              {props[tab].content.map((element) => (
                <ListGroup.Item key={uuidv4()}>
                  {element.username}
                </ListGroup.Item>
              ))}
            </ListGroup>
          </Col>
        </Row>
      </Container>
    </>
  );
};

export default Network;
