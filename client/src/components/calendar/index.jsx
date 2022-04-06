import React from "react";
import { Container, Row, Col, Button } from "react-bootstrap";
import { CheckCircle } from "react-feather";

import { Model } from "../calendar/model";

const slots = { 1: "Morning", 2: "Midday", 3: "Twilight" };
const days = {
  0: "Sunday",
  1: "Monday",
  2: "Tuesday",
  3: "Wednesday",
  4: "Thursday",
  5: "Friday",
  6: "Saturday",
};

const Slot = ({
  day = null,
  value = 0,
  available = true,
  onClick = () => {},
}) => {
  const color = available ? "bg-primary" : "bg-light";
  return (
    <div
      style={{
        height: "100%",
        width: "100%",
        borderRadius: "8px",
      }}
      className={`${color} shadow`}
      onClick={onClick}
    >
      {available && <CheckCircle className="text-light" size={18} />}
    </div>
  );
};

const Calendar = (props) => {
  props = { ...props, ...Model };
  const [state, setState] = React.useState(props);

  const pad = 3;

  const toggleSlot = (date, slot) => {
    const entry = state.content.find((element) => element.date === date);
    let available;
    if (entry.available.includes(slot)) {
      available = entry.available.filter((element) => element !== slot);
    } else {
      available = [...entry.available, slot];
    }
    state.content[entry.index] = { ...entry, date, available };
    setState({ ...state });
  };

  return (
    <>
      <Container className="text-center">
        <Row className={`mb-${pad}`}>
          <Col className="col-3"></Col>
          {Object.values(slots).map((slot) => (
            <Col className="text-muted">{slot}</Col>
          ))}
        </Row>
        {props.content.map((day) => {
          const date = new Date(day.date);
          return (
            <Row
              className={`mb-${pad}`}
              style={{
                height: "4rem",
              }}
            >
              <Col
                className="col-3"
                style={{
                  paddingTop: "auto",
                }}
              >
                <Row>
                  <Col>
                    <small>{days[date.getDay()]}</small>
                  </Col>
                  <Col className="text-muted">{day.date}</Col>
                </Row>
              </Col>
              {Object.entries(slots).map(([value, label], index) => (
                <Col>
                  <Slot
                    day={day.date}
                    value={index + 1}
                    onClick={(e) => toggleSlot(day.date, index + 1)}
                    available={day.available.includes(index + 1)}
                  />
                </Col>
              ))}
            </Row>
          );
        })}
        <Row>
          <Col className="d-grid gap-2 mt-4">
            <Button variant="outline-dark" className="shadow">
              Save Changes
            </Button>
          </Col>
        </Row>

        {/* {["Morning", "Midday", "Twilight"].reverse().map((timeslot) => (
          <Row>
            <Col xs className="col-3">
              {timeslot}
            </Col>
            {days.map((element) => {
              const color =
                Math.random() > 0.5 ? "var(--bs-success)" : "var(--bs-light)";
              return (
                <Col
                  style={{
                    backgroundColor: color,
                    border: "1px solid var(--bs-gray-100)",
                    borderRadius: "4px",
                  }}
                ></Col>
              );
            })}
          </Row>
        ))}
        <Row>
          <Col xs className="col-3"></Col>
          {days.map((element) => (
            <Col>{element}</Col>
          ))}
        </Row> */}
      </Container>
    </>
  );
};

export default Calendar;
