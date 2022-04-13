import React from "react";
import { Container, Row, Col } from "react-bootstrap";

import { API } from "../../constants";
import { Model } from "../calendar/model";

// TODO: enum
const slots = { 1: "Morning", 2: "Midday", 3: "Twilight" };

const CalendarCell = ({
  day = null,
  value = 0,
  available = true,
  onClick = () => {},
}) => {
  const color = available ? "bg-primary" : "bg-light";

  const handleClick = (e) => {
    console.log(date, time, available);
    onClick(date, time, !available);
  };

  return (
    <div
      style={{
        height: "100%",
        width: "100%",
        borderRadius: "8px",
      }}
      className={`${color} shadow`}
      onClick={handleClick}
    ></div>
  );
};

const Calendar = (props) => {
  props = { ...props, ...Model };
  const [state, setState] = React.useState(props);
  const [semaphore, setSemaphore] = React.useState(0);

  React.useEffect(() => {
    gofetch();
  }, [semaphore]);

  const gofetch = () => {
    const url =
      `${API}/calendar/query?` +
      new URLSearchParams({
        fk: 1,
      }).toString();
    fetch(url, {
      method: "POST",
    })
      .then((response) => response.json())
      .then((json) => {
        setState(json.data);
      })
      .catch((error) => {
        console.error(error);
      });
  };

  const pad = 3;

  const toggleSlot = (date, time, available) => {
    const url = `${API}/calendar/availability`;
    fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        fk: 1,
        date: date,
        time: time,
        available: available,
      }),
    })
      .then((response) => response.json())
      .then((json) => {
        setSemaphore(semaphore + 1);
      })
      .catch((error) => {
        console.error(error);
      });
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
        {state.content.map((day) => {
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
                  <CalendarCell
                    day={day.date}
                    value={index + 1}
                    onClick={(e) =>
                      toggleSlot(
                        day.date,
                        index + 1,
                        !day.available.includes(index + 1)
                      )
                    }
                    available={day.available.includes(index + 1)}
                  />
                </Col>
              ))}
            </Row>
          );
        })}
        <Row>
          <Col className="d-grid gap-2 mt-4">
            <small>Changes are saved automatically</small>
          </Col>
        </Row>
      </Container>
    </>
  );
};

export default Calendar;
