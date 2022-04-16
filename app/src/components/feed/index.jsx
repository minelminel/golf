import React from "react";
import { v4 as uuidv4 } from "uuid";
import { Container, Row, Col, Button, ListGroup } from "react-bootstrap";
import { Calendar, Search, User, Grid, Share2 } from "react-feather";

function Feed() {
  return (
    <>
      <Container>
        <Row>
          <Col className="d-grid gap-2">
            <Button
              className="mb-3 shadow"
              style={{
                height: "4rem",
                fontSize: "large",
              }}
              variant="success"
            >
              <User />
              &nbsp;My Profile
            </Button>
          </Col>
        </Row>
        <Row>
          <Col className="d-grid gap-2">
            <Button
              className="mb-3 shadow"
              style={{
                height: "4rem",
                fontSize: "large",
              }}
              variant="primary"
            >
              <Calendar />
              &nbsp;My Calendar
            </Button>
          </Col>
        </Row>
        <Row>
          <Col className="d-grid gap-2">
            <Button
              className="mb-3 shadow"
              style={{
                height: "4rem",
                fontSize: "large",
              }}
              variant="dark"
            >
              <Share2 />
              &nbsp;My Network
            </Button>
          </Col>
        </Row>
        <Row>
          <Col className="d-grid gap-2">
            <Button
              className="mb-3 shadow"
              style={{
                height: "4rem",
                fontSize: "large",
              }}
              variant="secondary"
            >
              <Search />
              &nbsp; Find Players
            </Button>
          </Col>
        </Row>
        <Row>
          <Col>
            <ListGroup variant="flush">
              <ListGroup.Item>Cras justo odio</ListGroup.Item>
              <ListGroup.Item>Dapibus ac facilisis in</ListGroup.Item>
              <ListGroup.Item>Morbi leo risus</ListGroup.Item>
              <ListGroup.Item>Porta ac consectetur ac</ListGroup.Item>
            </ListGroup>
          </Col>
        </Row>
      </Container>
    </>
  );
}

export default Feed;
