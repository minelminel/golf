import React from "react";
import { Container, Row, Col, Button } from "react-bootstrap";

import { Model } from "../calendar/model";

// TODO: enum
const slots = { 1: "Morning", 2: "Midday", 3: "Twilight" };

const Availability = ({
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
    ></div>
  );
};

const Calendar = (props) => {
  props = { ...props, ...Model };
  const [state, setState] = React.useState(props);

  React.useEffect(() => {
    loadPage();
  }, []);

  const loadPage = () => {
    console.log(`loadPage`);
    const url =
      `http://localhost:4000/calendar/query?` +
      new URLSearchParams({
        fk: 1,
      }).toString();
    console.log(url);
    fetch(url, {
      method: "POST",
    })
      .then((response) => response.json())
      .then((json) => {
        console.log(json);
        setState(json.data);
      })
      .catch((error) => {
        console.error(error);
      });
  };

  const pad = 3;

  const toggleSlot = (date, slot) => {
    console.log(date, slot);
    // const entry = state.content.find((element) => element.date === date);
    // let available;
    // if (entry.available.includes(slot)) {
    //   available = entry.available.filter((element) => element !== slot);
    // } else {
    //   available = [...entry.available, slot];
    // }
    // state.content[entry.index] = { ...entry, date, available };
    // setState({ ...state });
  };

  return (
    <>
      <Container className="text-center">
        <Row className={`mb-${pad}`}>
          <Col className="col-3">
            <span
              style={{
                fontSize: "small",
              }}
            >
              🟦 indicates <em>available</em>
            </span>
          </Col>
          {Object.values(slots).map((slot) => (
            <Col className="text-muted">{slot}</Col>
          ))}
        </Row>
        {props.content.map((day) => {
          const date = new Date(day.date);
          const month = date
            .toLocaleString("default", { month: "long" })
            .slice(0, 3);
          const weekday = date
            .toLocaleString("default", { weekday: "long" })
            .slice(0, 3);
          return (
            <Row
              className={`mb-${pad}`}
              style={{
                height: "4rem",
              }}
            >
              <Col
                className="col-3 middle"
                style={{
                  padding: "0 auto",
                }}
              >
                <Row>
                  <Col>
                    <small>{`${weekday}, ${month} ${date.getDate()}`}</small>
                  </Col>
                </Row>
              </Col>
              {Object.entries(slots).map(([value, label], index) => (
                <Col>
                  <Availability
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
