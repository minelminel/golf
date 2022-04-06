import React from "react";
import { v4 as uuidv4 } from "uuid";
import {
  Container,
  Row,
  Col,
  Form,
  Button,
  InputGroup,
  FormControl,
  Tabs,
  Tab,
  Carousel,
  Spinner,
} from "react-bootstrap";

const Home = ({ ready, handleLoginOrRegister = () => {} }) => {
  const submit = (e) => {
    e.preventDefault();
    const source = e.target.id;
    const fields = {
      register: {
        username: "register.username",
        email: "register.email",
        password: "register.password",
      },
      login: {
        username: "login.username",
        password: "login.password",
      },
    };
    const payload = Object.fromEntries(
      Object.entries(fields[source]).map(([key, value]) => [
        key,
        e.target[value]?.value,
      ])
    );
    fetch(`http://localhost:4000/auth/${source}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    })
      .then((response) => response.json())
      .then((json) => {
        handleLoginOrRegister(json);
      });
    console.log(source, payload);
  };
  return (
    <>
      <Container>
        <Row>
          <Col className="text-center">
            <Carousel
              variant="light"
              style={{
                height: "300px",
              }}
            >
              <Carousel.Item>
                <img
                  className="d-block w-100"
                  src="https://images.unsplash.com/photo-1535131749006-b7f58c99034b?ixlib=rb-1.2.1&ixid=MnwxMjA3fDB8MHxzZWFyY2h8M3x8Z29sZnxlbnwwfHwwfHw%3D&auto=format&fit=crop&w=900&q=60"
                  alt="First slide"
                />
                <Carousel.Caption>
                  <h5>First slide label</h5>
                  <p>
                    Nulla vitae elit libero, a pharetra augue mollis interdum.
                  </p>
                </Carousel.Caption>
              </Carousel.Item>
              <Carousel.Item>
                <img
                  className="d-block w-100"
                  src="https://images.unsplash.com/photo-1500932334442-8761ee4810a7?ixlib=rb-1.2.1&ixid=MnwxMjA3fDB8MHxzZWFyY2h8Mnx8Z29sZnxlbnwwfHwwfHw%3D&auto=format&fit=crop&w=900&q=60"
                  alt="Second slide"
                />
                <Carousel.Caption>
                  <h5>Second slide label</h5>
                  <p>
                    Lorem ipsum dolor sit amet, consectetur adipiscing elit.
                  </p>
                </Carousel.Caption>
              </Carousel.Item>
              <Carousel.Item>
                <img
                  className="d-block w-100"
                  src="https://images.unsplash.com/photo-1587174486073-ae5e5cff23aa?ixlib=rb-1.2.1&ixid=MnwxMjA3fDB8MHxzZWFyY2h8NXx8Z29sZnxlbnwwfHwwfHw%3D&auto=format&fit=crop&w=900&q=60"
                  alt="Third slide"
                />
                <Carousel.Caption>
                  <h5>Third slide label</h5>
                  <p>
                    Praesent commodo cursus magna, vel scelerisque nisl
                    consectetur.
                  </p>
                </Carousel.Caption>
              </Carousel.Item>
            </Carousel>
          </Col>
        </Row>
        <Row>
          <Col>
            <p>
              Lorem, ipsum dolor sit amet consectetur adipisicing elit.
              Voluptatum autem libero soluta dignissimos temporibus optio
              voluptas dicta beatae minima sint vel cum sit magni, ipsa natus
              quasi quibusdam totam minus.
            </p>
          </Col>
        </Row>
        <Row className="mb-2">
          <Col>
            <Tabs
              fill
              variant="tabs"
              defaultActiveKey="register"
              onSelect={() => {
                // allow tab change to propagate before checking resize
                setTimeout(() => {
                  window.scrollTo(0, document.body.scrollHeight);
                }, 25);
              }}
            >
              {/* REGISTER */}
              <Tab eventKey="register" title="Register" className="mt-4">
                <p>Start finding players now!</p>
                <Form onSubmit={submit} id="register">
                  <Form.Group>
                    <InputGroup className="mb-3">
                      <InputGroup.Text>@</InputGroup.Text>
                      <FormControl
                        placeholder="Username"
                        id="register.username"
                        required
                      />
                    </InputGroup>
                  </Form.Group>
                  <Form.Group className="mb-3">
                    <Form.Label>Email address</Form.Label>
                    <Form.Control
                      type="email"
                      placeholder="Enter email"
                      id="register.email"
                      required
                    />
                    <Form.Text className="text-muted">
                      No spam, we promise
                    </Form.Text>
                  </Form.Group>

                  <Form.Group className="mb-3">
                    <Form.Label>Password</Form.Label>
                    <Form.Control
                      type="password"
                      placeholder="Password"
                      id="register.password"
                      required
                    />
                  </Form.Group>
                  <Button variant="primary" type="submit" disabled={!ready}>
                    {!ready && <Spinner size="sm" animation="border" />}
                    {ready ? "Sign Up" : " Loading..."}
                  </Button>
                </Form>
              </Tab>
              {/* LOGIN */}
              <Tab eventKey="login" title="Login" className="mt-4">
                <p>Welcome back!</p>
                <Form onSubmit={submit} id="login">
                  <Form.Group>
                    <InputGroup className="mb-3">
                      <InputGroup.Text>@</InputGroup.Text>
                      <FormControl
                        placeholder="Username"
                        required
                        id="login.username"
                        value={`alice`}
                      />
                    </InputGroup>
                  </Form.Group>

                  <Form.Group className="mb-4">
                    <Form.Label>Password</Form.Label>
                    <Form.Control
                      type="password"
                      placeholder="Password"
                      id="login.password"
                      required
                      value={`alice`}
                    />
                  </Form.Group>
                  <Button variant="primary" type="submit" disabled={!ready}>
                    {!ready && <Spinner size="sm" animation="border" />}
                    {ready ? "Login" : " Loading..."}
                  </Button>

                  <Form.Group className="mb-3 mt-3">
                    <Form.Text>
                      <a className="text-muted" href="/">
                        Forgot your password?
                      </a>
                    </Form.Text>
                  </Form.Group>
                </Form>
              </Tab>
            </Tabs>
          </Col>
          <hr className="mt-4" />
        </Row>
      </Container>
    </>
  );
};

export default Home;
