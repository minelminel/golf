import React from "react";
import { Form, Button, Row, Col, ListGroup, Container } from "react-bootstrap";
import { v4 as uuidv4 } from "uuid";

import { Model } from "./model";

const Search = (props) => {
  const [state, setState] = React.useState({
    content: [
      {
        pk: 2,
        username: "bob",
      },
      {
        pk: 3,
        username: "earl",
      },
      {
        pk: 4,
        username: "fred",
      },
    ],
    metadata: {
      page: 0,
      pages: 0,
      size: 10,
      total: 0,
    },
    query: {
      radius: 25,
    },
  });

  const handleSearch = (e) => {
    e.preventDefault();
    console.log("handle search");
    console.log(e.target.radius.value);
  };

  return (
    <>
      <Container>
        <Form onSubmit={(e) => handleSearch(e)}>
          <Form.Group className="mb-3">
            <Form.Label>
              Distance from me: {`${state.query.radius}`} miles
            </Form.Label>
            <Form.Range
              id="radius"
              min={5}
              step={1}
              max={100}
              value={state?.query?.radius || 25}
              onChange={(e) =>
                setState({ ...state, query: { radius: e.target.value } })
              }
            />
          </Form.Group>

          <Form.Group className="d-grid gap-2">
            <Button variant="primary" type="submit" className="shadow">
              Search
            </Button>
          </Form.Group>
        </Form>

        <ListGroup className="mt-3" variant="flush">
          {state.content.map((element) => (
            <ListGroup.Item key={uuidv4()}>{element.username}</ListGroup.Item>
          ))}
        </ListGroup>
      </Container>
    </>
  );
};

export default Search;
