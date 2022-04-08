import React from "react";
import { Container, Row, Col, Button } from "react-bootstrap";
import { v4 as uuidv4 } from "uuid";
import { ShoppingCart, Coffee, CloudRain, UserPlus, Mail } from "react-feather";
// import { MapContainer, TileLayer, Marker, Popup } from "react-leaflet";

import { API } from "../../constants";
import { Model } from "./model";

const state = {
  user: {
    pk: 1,
    username: "alice",
  },
};

const Enums = {
  ridewalk: {
    0: <ShoppingCart />,
    1: <ShoppingCart />,
    2: <ShoppingCart />,
  },
  drinking: {
    0: <Coffee />,
    1: <Coffee />,
    2: <Coffee />,
    3: <Coffee />,
  },
  weather: {
    0: <CloudRain />,
    1: <CloudRain />,
    2: <CloudRain />,
    3: <CloudRain />,
  },
  calendar: {
    0: "",
    1: "morning",
    2: "midday",
    3: "twilight",
  },
  days: {
    0: "S",
    1: "M",
    2: "T",
    3: "W",
    4: "T",
    5: "F",
    6: "S",
  },
};

const between = "1rem";

const CalendarDay = (props) => {
  const date = new Date(props.date);
  const open = props.available.length > 0;
  return (
    <span
      style={{
        fontWeight: open ? `bolder` : `inherit`,
        borderBottom: open ? "2px solid black" : "inherit",
      }}
    >
      {Enums.days[date.getDay()]}
    </span>
  );
};

const btnStyle = {
  borderRadius: "25px",
  height: "3rem",
};

const actionButtonsEnabled = false;

const Profile = () => {
  const props = Model;
  return (
    <>
      <Container>
        <Row className="text-center align-items-center">
          {actionButtonsEnabled && (
            <Col>
              <Button
                variant="outline-success"
                style={btnStyle}
                className="shadow"
              >
                <UserPlus />
              </Button>
            </Col>
          )}
          <Col className="text-center">
            <div className="frame mb-3">
              <img
                src={`${API}/images/1`}
                className="cropped"
                style={{
                  width: "124px",
                  height: "124px",
                }}
              />
            </div>
            <h3
              className="mb-0"
              style={{
                whiteSpace: "nowrap",
              }}
            >
              Alice
            </h3>
            <span className="text-muted">@{state.user.username}</span>
          </Col>
          {actionButtonsEnabled && (
            <Col>
              <Button
                variant="outline-primary"
                style={btnStyle}
                className="shadow"
              >
                <Mail />
              </Button>
            </Col>
          )}
        </Row>
        <Row>
          <Col>
            <Container
              className="mt-4 shadow"
              style={{
                borderRadius: "15px",
                padding: "15px",
              }}
            >
              <Row className="mb-4">
                <Col>
                  <span>71 connections</span>
                </Col>
                <Col className="text-center">
                  <span
                    className="shadow"
                    style={{
                      display: "flex",
                      justifyContent: "center",
                      alignItems: "center",
                      position: "absolute",
                      transform: "translate(60%, -60%)",
                      width: "5rem",
                      height: "5rem",
                      borderRadius: "50%",
                      backgroundColor: "var(--bs-gray-300)",
                      fontSize: "1.75rem",
                      fontWeight: "bold",
                    }}
                  >
                    3.2
                  </span>
                </Col>
              </Row>
              <Row>
                <Col xs lg={2} xs={2}>
                  <ul>
                    <li
                      style={{
                        marginTop: between,
                        marginBottom: between,
                      }}
                      key={uuidv4()}
                    >
                      {Enums.ridewalk[props.profile.ridewalk]}
                    </li>
                    <li
                      style={{
                        marginTop: between,
                        marginBottom: between,
                      }}
                      key={uuidv4()}
                    >
                      {Enums.drinking[props.profile.drinking]}
                    </li>
                    <li
                      style={{
                        marginTop: between,
                        marginBottom: between,
                      }}
                      key={uuidv4()}
                    >
                      {Enums.weather[props.profile.weather]}
                    </li>
                  </ul>
                </Col>
                <Col>
                  <ul>
                    {props.profile.prompts.map((prop) => (
                      <li key={uuidv4()} className="mb-3">
                        <div>{prop.a}</div>
                        <small>—{prop.q}</small>
                      </li>
                    ))}
                  </ul>
                </Col>
              </Row>
              <Row className="text-center mt-2">
                {props.calendar.content.map((prop) => (
                  <Col key={uuidv4()}>
                    <CalendarDay {...prop} />
                  </Col>
                ))}
              </Row>
            </Container>
          </Col>
        </Row>
        <Row>
          <Col>
            <div
              className="mt-4 shadow"
              style={{
                borderRadius: "15px",
                height: "100px",
                backgroundImage:
                  "url(https://www.cloudways.com/blog/wp-content/uploads/MapPress-Easy-Google-Map-Plugin.jpg)",
              }}
            ></div>
          </Col>
        </Row>
      </Container>
    </>
  );
};

export default Profile;
