import React from "react";
import "./App.css";
import "bootstrap/dist/css/bootstrap.min.css";
// import "leaflet/dist/leaflet.css";
import { Container, Row, Col } from "react-bootstrap";
import { ToastContainer, toast } from "react-toastify";
import "react-toastify/dist/ReactToastify.css";

import Navigation from "./components/navigation";
import Conversations from "./components/conversations";
import Conversation from "./components/conversation";
import Profile from "./components/profile";
import Feed from "./components/feed";
import Home from "./components/home";
import Calendar from "./components/calendar";
import Search from "./components/search";
import Network from "./components/network";

const view = [
  "Home",
  "Feed",
  "Network",
  "Calendar",
  "Profile",
  "Inbox",
  "Chat",
  "Search",
][3];

function App() {
  const [authenticated, setAuthenticated] = React.useState(false);
  const [state, setState] = React.useState({
    // AUTHENTICATION
    auth: {
      data: {
        token:
          "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOjEwNiwiYXVkIjpudWxsLCJleHAiOjE2NDkwODE4MzkzMDIsIm5iZiI6MTY0OTA3ODIzOTMwMiwiaWF0IjoxNjQ5MDc4MjM5MzAyLCJqdGkiOm51bGx9.0DoN63E3M0OziVsIKyYl7MFrFo5Un8dvuJTKURpa5fo",
      },
      error: null,
      ready: true,
    },
    // SESSION
    user: {
      data: {
        pk: 1,
        username: "alice",
      },
      error: null,
      ready: false,
    },
    // PROFILE
    profile: {
      data: {
        handicap: 0.0,
        // ...
      },
      error: null,
      ready: false,
    },
    // ALL CONVERSATIONS
    inbox: {
      data: {
        content: [],
        metadata: {},
      },
      error: null,
      ready: false,
    },
    // SINGLE CONVERSATION
    chat: {
      data: {
        content: [],
        metadata: {},
      },
      error: null,
      ready: false,
    },
    // AVAILABILITY
    calendar: {
      data: {
        content: [],
        metadata: {},
      },
      error: null,
      ready: false,
    },
    // OUR LOCATION
    location: {
      data: {},
      error: null,
      ready: false,
    },
  });

  const notify = (e) => {
    toast(e);
  };

  const handleLoginOrRegister = ({ data, error, ready = true }) => {
    // store token for session
    console.log(data, error, ready);
    setState({ ...state, auth: { data, error, ready } });
  };

  console.log(`~ s t a t e ~`);
  console.log(state);

  return (
    <>
      <Container className="h-100">
        <Row className="justify-content-md-center h-100">
          <Col
            // xs
            xl={5}
            lg={7}
            md={9}
            sm={11}
            className="shadow"
            style={{
              borderLeft: "1px solid #e7e7e7",
              borderRight: "1px solid #e7e7e7",
              backgroundColor: "var(--bs-light)",
            }}
          >
            <ToastContainer />
            {view === "Home" && (
              <>
                <Navigation
                  brand={{ text: "Whose ⛳️ Away", type: "title" }}
                  timeline={{ enabled: false }}
                  messages={{ enabled: false }}
                />
                <Home
                  notify={notify}
                  ready={state.auth.ready}
                  handleLoginOrRegister={handleLoginOrRegister}
                />
              </>
            )}
            {view === "Inbox" && (
              <>
                <Navigation brand={{ text: "Inbox", type: "title" }} />
                <Conversations />
              </>
            )}
            {view === "Chat" && (
              <>
                <Navigation brand={{ text: "@bob", type: "title" }} />
                <Conversation />
              </>
            )}
            {view === "Profile" && (
              <>
                <Navigation
                  brand={{ text: "Active 2 days ago", type: "info" }}
                />
                <Profile />
              </>
            )}
            {view === "Feed" && (
              <>
                <Navigation brand={{ text: "Feed", type: "title" }} />
                <Feed />
              </>
            )}
            {view === "Calendar" && (
              <>
                <Navigation brand={{ text: "Calendar", type: "title" }} />
                <Calendar />
              </>
            )}
            {view === "Search" && (
              <>
                <Navigation brand={{ text: "Search", type: "title" }} />
                <Search />
              </>
            )}
            {view === "Network" && (
              <>
                <Navigation brand={{ text: "My Network", type: "title" }} />
                <Network />
              </>
            )}
          </Col>
        </Row>
      </Container>
    </>
  );
}

export default App;
