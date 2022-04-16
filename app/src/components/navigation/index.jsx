import React from "react";
import { Navbar, Container, Nav, Spinner, Badge } from "react-bootstrap";
import { Layers, Box } from "react-feather";

import { Model } from "./model";

const Navigation = (props) => {
  props = { ...Model, ...props };
  // console.log(props);
  return (
    <>
      <Navbar
        className="mt-1 mb-3 shadow"
        expand="lg"
        variant="light"
        bg="light"
        sticky="top"
        style={{
          fontWeight: "bolder",
          borderRadius: "8px",
        }}
      >
        <Container>
          <Nav.Link href={props.timeline.href}>
            {props.timeline.enabled && <Layers />}
          </Nav.Link>
          {props.loading ? (
            <Spinner animation="border" variant="primary" size="sm" />
          ) : props.brand.type === "title" ? (
            <Navbar.Brand className="mx-0">{props.brand.text}</Navbar.Brand>
          ) : (
            <Navbar.Text className="text-muted small">
              {props.brand.text}
            </Navbar.Text>
          )}
          <Nav.Link>
            {props.messages.enabled && (
              <>
                <Box />
                <Badge
                  pill
                  bg="danger"
                  style={{
                    position: "absolute",
                    transform: "translate(-50%, -25%)",
                    fontSize: "x-small",
                  }}
                >
                  {props.messages.notifications}
                </Badge>
              </>
            )}
          </Nav.Link>
        </Container>
      </Navbar>
    </>
  );
};
export default Navigation;
