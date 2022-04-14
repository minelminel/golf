import React, { useState, useContext, createContext } from "react";
import {
  BrowserRouter,
  Route,
  Routes,
  Link,
  Navigate,
  Outlet,
  useNavigate,
  useParams,
  useLocation,
} from "react-router-dom";
import {
  Container,
  Nav,
  Navbar,
  NavDropdown,
  Badge,
  Row,
  Col,
  Button,
  ListGroup,
  Form,
  InputGroup,
  FormControl,
  Carousel,
  Tabs,
  Tab,
  ButtonGroup,
  Card,
} from "react-bootstrap";
// ICONS
import {
  Box,
  Layers,
  Send,
  UserPlus,
  Mail,
  ShoppingCart,
  Coffee,
  CloudRain,
  User,
  Search,
  Share,
} from "react-feather";
import { BsFillCalendarCheckFill } from "react-icons/bs";
import { FaBeer, FaWalking, FaCoffee } from "react-icons/fa";
import { BiDrink } from "react-icons/bi";
import { AiFillCar } from "react-icons/ai";
import {
  TiWeatherPartlySunny,
  TiWeatherSunny,
  TiWeatherShower,
} from "react-icons/ti";
// END ICONS
import { v4 as uuidv4 } from "uuid";
import { ToastContainer, toast } from "react-toastify";
import QRCode from "react-qr-code";

import { formatTimeSince } from "./utils";

import "react-toastify/dist/ReactToastify.css";
import "bootstrap/dist/css/bootstrap.min.css";
import "leaflet/dist/leaflet.css";
import "./App.css";

import {
  MapContainer,
  Marker,
  Popup,
  TileLayer,
  Pane,
  Circle,
} from "react-leaflet";

const CONST = {
  API: `http://192.168.1.114:4000`,
  DEBUG: false,
};

const ROUTES = {
  HOME: "/",
  TIMELINE: "/timeline",
  USER: "/user",
  NETWORK: "/network",
  CALENDAR: "/calendar",
  SEARCH: "/search",
  INBOX: "/inbox",
  CHAT: "/chat",
  SHARE: "/share",
  SETTINGS: "/settings",
};

const ENUMS = {
  mobility: {
    0: <FaWalking size={32} className="text-muted" />,
    1: <FaWalking size={32} />,
    2: <AiFillCar size={32} />,
  },
  drinking: {
    0: <FaBeer size={32} className="text-muted" />,
    1: <FaCoffee size={32} />,
    2: <FaBeer size={32} />,
    3: <BiDrink size={32} />,
  },
  weather: {
    0: <TiWeatherPartlySunny size={32} className="text-muted" />,
    1: <TiWeatherSunny size={32} />,
    2: <TiWeatherPartlySunny size={32} />,
    3: <TiWeatherShower size={32} />,
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

const DESCRIPTIONS = {
  mobility: {
    0: "No mobility preference",
    1: "Prefers walking",
    2: "Prefers cart",
  },
  drinking: {
    0: "No drinking preference",
    1: "Never drinks",
    2: "Light drinking",
    2: "Heavy drinking",
  },
  weather: {
    0: "No weather preference",
    1: "Perfect weather only",
    2: "Mild weather is fine",
    3: "Poor weather is fine",
  },
};

const requestProps = {
  data: null,
  error: null,
  status: null,
  timestamp: null,
};

const paginationProps = {
  ...requestProps,
  data: {
    content: [],
    metadata: {},
  },
};

/**
 * COMPONENTS
 */

const BannerBlock = (props) => {
  const { text, bg = "info", className } = props;
  return (
    <div
      className={`mb-3 bg-${bg} shadow ${className}`}
      style={{
        borderRadius: "5px",
        padding: "0.5rem",
        color: "black",
      }}
    >
      {text}
    </div>
  );
};

const RegisterForm = (props) => {
  const { handleSubmit, byline = "Get started!", loggedIn = false } = props;

  const onSubmit = (e) => {
    e.preventDefault();
    const { email, username, password } = e.target;
    handleSubmit({
      email: email.value,
      username: username.value,
      password: password.value,
    });
  };

  return (
    <Form onSubmit={onSubmit} id="register">
      <fieldset disabled={loggedIn}>
        {loggedIn && (
          <BannerBlock
            bg="warning"
            text={loggedIn ? "It looks like you're already logged in" : byline}
          />
        )}
        <Form.Group>
          <InputGroup className="mb-3 shadow">
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
            className="mb-2 shadow"
            type="email"
            placeholder="Enter email"
            id="register.email"
            required
          />
          <Form.Text className="text-muted">No spam, we promise</Form.Text>
        </Form.Group>

        <Form.Group className="mb-4">
          <Form.Label>Password</Form.Label>
          <Form.Control
            className="shadow"
            type="password"
            placeholder="Password"
            id="register.password"
            required
          />
        </Form.Group>
        <Button variant="primary" type="submit">
          Sign Up
        </Button>
      </fieldset>
    </Form>
  );
};

const LoginForm = (props) => {
  const { handleSubmit, byline = "Welcome Back", loggedIn = false } = props;

  const onSubmit = (e) => {
    e.preventDefault();
    const { username, password } = e.target;
    handleSubmit({ username: username.value, password: password.value });
  };

  return (
    <Form onSubmit={onSubmit} id="login">
      <fieldset disabled={loggedIn}>
        {loggedIn && (
          <BannerBlock
            bg="warning"
            text={loggedIn ? "It looks like you're already logged in" : byline}
          />
        )}
        <Form.Group>
          <InputGroup className="mb-3 shadow">
            <InputGroup.Text>@</InputGroup.Text>
            <FormControl
              placeholder="Username"
              required
              id="username"
              value={`alice`}
            />
          </InputGroup>
        </Form.Group>
        <Form.Group className="mb-4">
          <Form.Label>Password</Form.Label>
          <Form.Control
            className="shadow"
            type="password"
            placeholder="Password"
            id="password"
            required
            value={`password`}
          />
        </Form.Group>
        <Row>
          <Col>
            <Button variant="primary" type="submit">
              Login
            </Button>
          </Col>
          <Col>
            <Form.Text>
              <a className="text-muted" href="/">
                Forgot your password?
              </a>
            </Form.Text>
          </Col>
        </Row>
      </fieldset>
    </Form>
  );
};

const CalendarCell = (props) => {
  const { available = true, onClick = () => {} } = props;
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

const InboxItem = (props) => {
  const { ours, dst, src, read, body, created_at, onClick } = props;
  return (
    <ListGroup.Item
      as="li"
      className="d-flex mt-3 shadow"
      style={{
        borderRadius: "15px",
        paddingTop: "15px",
        paddingBottom: "15px",
      }}
      onClick={onClick}
    >
      <div className="frame ms-2">
        <img
          alt={`${ours ? dst?.username : src?.username}`}
          title={`/images/${ours ? dst?.username : src?.username}`}
          src={`${ours ? dst.image?.href : src.image?.href}`}
          className="cropped"
          style={{
            width: "36px",
            height: "36px",
          }}
        />
      </div>
      <div className="ms-3 me-auto">
        <div className="align-middle">
          <strong>@{ours ? dst?.username : src?.username}</strong>
          &nbsp;
          {ours && !read ? "🔵" : null}
        </div>
        {/* TODO: FIXME ellipsis */}
        <div>
          {ours ? `You: ` : ``}
          {body.length > 30 ? body.slice(0, 30) + "..." : body}
        </div>
      </div>
      <div
        className="text-muted float-right"
        style={{
          fontSize: "small",
          fontWeight: "bold",
          marginTop: "auto",
          marginBottom: "auto",
        }}
      >
        {formatTimeSince(created_at)}
      </div>
    </ListGroup.Item>
  );
};

const ChatBubble = (props) => {
  const { timestamp = false, ours } = props;
  return (
    <Row className={`justify-content-${ours ? "end" : "start"}`}>
      {timestamp && (
        <div
          className="text-center text-muted"
          style={{
            fontSize: "small",
            marginBottom: "0.5rem",
          }}
        >
          {formatTimeSince(props.created_at)}
        </div>
      )}
      {!ours && <small className="text-muted">@{props.src.username}</small>}
      <Col className="col-8">
        {/* show an optional timestamp */}
        <p
          className="shadow"
          style={{
            background: `var(--${ours ? "bs-secondary" : "bs-primary"})`,
            borderRadius: "10px",
            padding: "10px",
            color: "white",
          }}
        >
          {props.body}
        </p>
      </Col>
    </Row>
  );
};

const ChatInput = (props) => {
  const [input, setInput] = React.useState(``);

  const type = (e) => {
    setInput(e.target.value);
  };

  const send = (e) => {
    console.log(`Send: ${input}`);
    props.onSubmit(input);
    setInput(``);
  };

  return (
    <Row
      className="fixed-bottom"
      style={{
        margin: "0 auto",
        backgroundColor: "var(--bs-dark)",
        height: "6rem",
        width: "inherit",
      }}
    >
      <Col>
        <input
          onChange={type}
          value={input}
          as="textarea"
          rows={2}
          placeholder="Start typing..."
          style={{
            padding: "5px",
            borderRadius: "8px",
            border: "1px solid gray",
            width: "100%",
            marginTop: "0.5rem",
          }}
        />
      </Col>
      <Col xs={2} sm={2} md={2} lg={2} className="text-end">
        <Button
          disabled={input.length < 1}
          onClick={send}
          style={{
            borderRadius: "8px",
            marginTop: "0.5rem",
          }}
        >
          <Send size={20} />
        </Button>
      </Col>
    </Row>
  );
};

const CalendarDay = (props) => {
  const { date, available } = props;

  return (
    <span
      style={{
        fontWeight: available ? `bolder` : `inherit`,
        textUnderlineOffset: "5px",
        textDecoration: available ? "underline" : "none",
      }}
      className={available ? "fw-bold" : "text-muted"}
    >
      {ENUMS.days[new Date(date).getDay()]}
    </span>
  );
};

const CalendarTray = (props) => {
  // TODO: make this expandable to show details
  const { content } = props;

  const dates = new Set(
    content.map((cal) => new Date(cal.date).toLocaleDateString())
  );

  let loop = new Date(); // today
  loop.setHours(0);
  loop.setMinutes(0);
  loop.setSeconds(0);
  loop.setMilliseconds(0);

  return (
    <Row className="text-center mt-2">
      {new Array(7).fill(0).map((e) => {
        const date = loop.toLocaleDateString();
        const available = dates.has(date);
        loop.setDate(loop.getDate() + 1);
        console.log(date, available);
        return (
          <Col key={uuidv4()}>
            <CalendarDay date={date} available={available} />
          </Col>
        );
      })}
    </Row>
  );
};

const PreferenceTray = (props) => {
  const { profile = {} } = props;
  const { mobility, drinking, weather } = profile;
  return (
    <Row className="text-center mb-4">
      <Col>
        {ENUMS.mobility[mobility]}
        <div>{DESCRIPTIONS.mobility[mobility]}</div>
      </Col>
      <Col>
        {ENUMS.drinking[drinking]}
        <div>{DESCRIPTIONS.drinking[drinking]}</div>
      </Col>
      <Col>
        {ENUMS.weather[weather]}
        <div>{DESCRIPTIONS.weather[weather]}</div>
      </Col>
    </Row>
  );
};

const UserItem = (props) => {
  // TODO: handle action as atom component
  const {
    type, // followers,following
    action = () => {
      console.log(`default onClick`);
    }, // right gutter button
    onClick = () => {
      console.log(`default onClick`);
    },
    style = {},
    // user props
    pk,
    username,
    profile = {},
    location = {},
    image = {},
    calendar = [],
  } = props;

  return (
    <ListGroup.Item
      as="li"
      className="d-flex"
      style={{
        border: "none",
        ...style,
      }}
    >
      <Container className="p-0">
        <Row>
          <Col className="col-2">
            <div className="center">
              <img
                // alt={`${ours ? dst?.username : src?.username}`}
                // title={`/images/${ours ? dst?.username : src?.username}`}
                onClick={onClick}
                alt={`${username}`}
                title={`${username}`}
                src={
                  image?.href ||
                  `https://cdn.theatlantic.com/media/mt/science/cat_caviar.jpg`
                }
                className="cropped"
                style={{
                  width: "36px",
                  height: "36px",
                  cursor: "pointer",
                }}
              />
            </div>
          </Col>
          <Col>
            <Row>
              <span className="px-0">
                <span className="fw-bold">{profile.alias}&nbsp;</span>@
                {username}
              </span>
            </Row>
            <Row>
              <small className="px-0 text-muted">{location.label}</small>
            </Row>
            <Row>{profile.bio}</Row>
          </Col>
          <Col className="col-2">
            <div
              className="float-right center"
              style={{
                fontSize: "small",
                fontWeight: "bold",
                marginTop: "auto",
                marginBottom: "auto",
              }}
            >
              <Badge
                variant={action.variant}
                style={{ cursor: "pointer" }}
                onClick={action}
              >
                {type === "followers" ? "Follow" : "Unfollow"}
              </Badge>
            </div>
          </Col>
        </Row>
      </Container>
    </ListGroup.Item>
  );
};

const MapPanel = (props) => {
  const { distance, location = {} } = props;
  const { coordinates = [] } = location;
  const position = coordinates.slice().reverse();
  console.log(position);

  return (
    position.length && (
      <MapContainer
        center={position}
        zoom={9}
        scrollWheelZoom={false}
        style={{
          borderRadius: "15px",
        }}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        <Circle center={position} radius={10000} />
      </MapContainer>
    )
  );
};

// intentionally separate
const AuthContext = createContext();
//

const useAuth = () => {
  const getAuth = () => {
    const session = JSON.parse(sessionStorage.getItem("auth"));
    return { token: session?.token, pk: session?.pk };
  };

  const [auth, setAuth] = useState(getAuth());

  const saveAuth = (auth) => {
    sessionStorage.setItem("auth", JSON.stringify(auth));
    setAuth(auth);
  };

  const clearAuth = () => {
    toast("Logout successful", { type: "success" });
    saveAuth({});
  };

  return {
    auth,
    setAuth: saveAuth,
    resetAuth: clearAuth,
    isAuthed: () => !!auth?.pk || !!auth?.token, // FIXME
  };
};

const Navigation = (props) => {
  const { auth, resetAuth, isAuthed } = useContext(AuthContext);
  const [notifications, setNotifications] = useState();
  const navigate = useNavigate();
  const { brand } = props;

  React.useEffect(() => {
    isAuthed() && gofetch();
  }, []);

  const gofetch = () => {
    fetch(`${CONST.API}/notifications/${auth.pk}`, {
      method: "POST",
    })
      .then((response) => response.json())
      .then((json) => {
        setNotifications(json);
      })
      .catch((error) => {
        console.error(error);
        toast("Failed to fetch notifications", { type: "error" });
      });
  };
  return (
    <>
      <Navbar
        className="mt-1 mb-3 shadow"
        expand="lg"
        variant="dark"
        bg="dark"
        sticky="top"
        style={{
          fontWeight: "bolder",
          borderRadius: "8px",
        }}
      >
        <Container>
          {/* LEFT */}

          {isAuthed() ? (
            <NavDropdown title={<Layers />}>
              <NavDropdown.Item onClick={() => navigate(ROUTES.HOME)}>
                Home
              </NavDropdown.Item>
              <NavDropdown.Item onClick={() => navigate(ROUTES.TIMELINE)}>
                Timeline
              </NavDropdown.Item>
              <NavDropdown.Item
                onClick={() => navigate(`${ROUTES.USER}/${auth.pk}`)}
              >
                User
              </NavDropdown.Item>
              <NavDropdown.Item onClick={() => navigate(ROUTES.NETWORK)}>
                Network
              </NavDropdown.Item>
              <NavDropdown.Item onClick={() => navigate(ROUTES.SEARCH)}>
                Search
              </NavDropdown.Item>
              <NavDropdown.Item onClick={() => navigate(ROUTES.CALENDAR)}>
                Calendar
              </NavDropdown.Item>
              <NavDropdown.Item onClick={() => navigate(ROUTES.INBOX)}>
                Inbox
              </NavDropdown.Item>
              <NavDropdown.Divider />
              <NavDropdown.Item onClick={() => navigate(ROUTES.SETTINGS)}>
                Settings
              </NavDropdown.Item>
              <NavDropdown.Item onClick={resetAuth}>Log Out</NavDropdown.Item>
            </NavDropdown>
          ) : (
            <Navbar.Text></Navbar.Text>
          )}
          {/* CENTER */}
          {brand.type === "title" ? (
            <Navbar.Brand className="mx-0">{brand.text}</Navbar.Brand>
          ) : (
            <Navbar.Text className="text-muted small">{brand.text}</Navbar.Text>
          )}
          {/* RIGHT */}
          {isAuthed() ? (
            <Nav.Link>
              <Link to={ROUTES.INBOX}>
                <Box />
                {notifications?.data > 0 && (
                  <Badge
                    pill
                    bg="danger"
                    style={{
                      position: "absolute",
                      transform: "translate(-50%, -25%)",
                      fontSize: "x-small",
                    }}
                  >
                    {notifications?.data < 100 ? notifications.data : "99+"}
                  </Badge>
                )}
              </Link>
            </Nav.Link>
          ) : (
            <Navbar.Text></Navbar.Text>
          )}
        </Container>
      </Navbar>
    </>
  );
};

const Page = (props) => {
  const { title, children, className = "" } = props;

  React.useEffect(() => {
    // set page title
    document.title = title ? `⛳️ | ${title}` : `⛳️`;
  }, []);

  return (
    <>
      <Container className={`h-100 ${className}`}>
        <Row className="justify-content-md-center h-100">
          <Col
            xs
            sm={11}
            md={8}
            lg={7}
            xl={5}
            className="shadow"
            style={
              {
                // borderLeft: "1px solid #e7e7e7",
                // borderRight: "1px solid #e7e7e7",
                // backgroundColor: "var(--bs-light)",
              }
            }
          >
            <Navigation />
            {/* <h6 className="text-center text-muted">{title}</h6> */}
            {children}
          </Col>
        </Row>
      </Container>
    </>
  );
};

const HomePage = (props) => {
  const { setAuth, isAuthed } = useContext(AuthContext);

  const navigate = useNavigate();

  const handleRegister = (creds) => {
    fetch(`${CONST.API}/auth/register`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(creds),
    })
      .then((response) => response.json())
      .then((json) => {
        setAuth(json.data);
        toast("Register Successful", { type: "success" });
        navigate(ROUTES.TIMELINE, { replace: true });
      })
      .catch((error) => {
        console.error(error);
        toast("Register Failed", { type: "error" });
      });
  };

  const handleLogin = (creds) => {
    fetch(`${CONST.API}/auth/login`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(creds),
    })
      .then((response) => response.json())
      .then((json) => {
        setAuth(json.data);
        toast("Login Successful", { type: "success" });
        navigate(ROUTES.TIMELINE, { replace: true });
      })
      .catch((error) => {
        console.error(error);
        toast("Login Failed", { type: "error" });
      });
  };

  return (
    <Page title="Home">
      <Row>
        <Col className="text-center mb-3">
          <Carousel variant="light">
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
                <p>Lorem ipsum dolor sit amet, consectetur adipiscing elit.</p>
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
            Lorem, ipsum dolor sit amet consectetur adipisicing elit. Voluptatum
            autem libero soluta dignissimos temporibus optio voluptas dicta
            beatae minima sint vel cum sit magni, ipsa natus quasi quibusdam
            totam minus.
          </p>
        </Col>
      </Row>
      <Row className="mb-2">
        <Col>
          <Tabs
            fill
            variant="tabs"
            defaultActiveKey="login"
            onSelect={() => {
              // allow tab change to propagate before checking resize
              setTimeout(() => {
                window.scrollTo(0, document.body.scrollHeight);
              }, 25);
            }}
          >
            {/* REGISTER */}
            <Tab eventKey="register" title="Register" className="mt-4">
              <RegisterForm
                handleSubmit={handleRegister}
                loggedIn={isAuthed()}
              />
            </Tab>
            {/* LOGIN */}
            <Tab eventKey="login" title="Login" className="mt-4">
              <LoginForm handleSubmit={handleLogin} loggedIn={isAuthed()} />
            </Tab>
          </Tabs>
        </Col>
      </Row>
      <Row
        style={{
          height: "2rem",
        }}
      ></Row>
    </Page>
  );
};

const TimelinePage = (props) => {
  const { auth, isAuthed } = useContext(AuthContext);
  const [state, setState] = useState({});

  const navigate = useNavigate();

  return (
    <Page title="Timeline">
      <pre>{JSON.stringify(state?.data, null, 2)}</pre>
      <Row className="mb-3" style={{ height: "4rem" }}>
        <Col className="d-grid">
          <Button
            variant="success"
            onClick={() => navigate(`${ROUTES.USER}/${auth.pk}`)}
          >
            <User />
            &nbsp;<small>My Profile</small>
          </Button>
        </Col>
        <Col className="d-grid">
          <Button variant="primary" onClick={() => navigate(ROUTES.CALENDAR)}>
            <BsFillCalendarCheckFill />
            &nbsp;<small>My Calendar</small>
          </Button>
        </Col>
      </Row>
      <Row className="mb-3" style={{ height: "4rem" }}>
        <Col className="d-grid">
          <Button variant="secondary" onClick={() => navigate(ROUTES.SEARCH)}>
            <Search />
            &nbsp;<small>Search</small>
          </Button>
        </Col>
        <Col className="d-grid">
          <Button variant="light" onClick={() => navigate(ROUTES.SHARE)}>
            <Share />
            &nbsp;<small>Share</small>
          </Button>
        </Col>
      </Row>
      <Row>
        <Col>Content</Col>
      </Row>
    </Page>
  );
};

const UserPage = (props) => {
  const { auth, isAuthed } = useContext(AuthContext);
  const [state, setState] = useState(requestProps);
  const { pk } = useParams();

  const navigate = useNavigate();

  const between = "1rem";

  React.useEffect(() => {
    gofetch();
  }, []);

  const gofetch = () => {
    fetch(`${CONST.API}/users/${pk}`, {
      method: "GET",
    })
      .then((response) => response.json())
      .then((json) => setState(json))
      .catch((error) => {
        console.error(error);
        toast("Error fetching user", { type: "error" });
      });
  };

  // is this our own profile? are we logged in?
  const isMe = isAuthed() && auth.pk === parseInt(pk);

  const leftActionButton =
    isAuthed() && !isMe ? (
      <Button
        variant="outline-success"
        style={{
          borderRadius: "25px",
          height: "3rem",
        }}
        className="shadow"
      >
        <UserPlus />
      </Button>
    ) : null;

  const rightActionButton =
    isAuthed() && !isMe ? (
      <Button
        variant="outline-primary"
        style={{
          borderRadius: "25px",
          height: "3rem",
        }}
        className="shadow"
      >
        <Mail />
      </Button>
    ) : (
      <Button
        variant="outline-primary"
        style={{
          borderRadius: "25px",
          height: "3rem",
        }}
        className="shadow"
        onClick={() => navigate(ROUTES.SETTINGS)}
      >
        Edit
      </Button>
    );

  return (
    <Page title="User">
      <Row className="text-center align-items-center">
        <Col>{leftActionButton}</Col>
        <Col className="text-center">
          <div className="frame mb-3">
            <img
              src={state.data?.image?.href}
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
            {state.data?.profile?.alias}
          </h3>
          <span className="text-muted">@{state.data?.username}</span>
        </Col>
        <Col>{rightActionButton}</Col>
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
              <Col xs>
                <small>{state.data?.profile?.bio}</small>
              </Col>
              <Col className="text-center">
                <span
                  className="shadow"
                  style={{
                    display: "flex",
                    justifyContent: "center",
                    alignItems: "center",
                    position: "absolute",
                    transform: "translate(70%, -50%)",
                    width: "5rem",
                    height: "5rem",
                    borderRadius: "50%",
                    backgroundColor: "var(--bs-gray-300)",
                    fontSize: "1.75rem",
                    fontWeight: "bold",
                    color: "black",
                  }}
                >
                  3.2
                </span>
              </Col>
            </Row>
            <PreferenceTray profile={state.data?.profile} />
            {/* <Row className="text-center">
              <Col>{Enums.mobility[state.data?.profile.mobility]}</Col>
              <Col>{Enums.drinking[state.data?.profile.drinking]}</Col>
              <Col>{Enums.weather[state.data?.profile.weather]}</Col>
            </Row> */}
            <CalendarTray content={state.data?.calendar || []} />
          </Container>
        </Col>
      </Row>
      <Row>
        <Col>
          <div
            className="mt-4 shadow"
            style={{
              height: "160px",
              // backgroundImage:
              // "url(https://www.cloudways.com/blog/wp-content/uploads/MapPress-Easy-Google-Map-Plugin.jpg)",
            }}
          >
            <MapPanel {...(state.data?.location || {})} />
          </div>
        </Col>
      </Row>
      {/* <pre>{JSON.stringify(state?.data, null, 2)}</pre> */}
    </Page>
  );
};

const NetworkPage = (props) => {
  const { auth } = useContext(AuthContext);
  const [followers, setFollowers] = useState(paginationProps);
  const [following, setFollowing] = useState(paginationProps);

  React.useEffect(() => {
    fetchFollowers();
    fetchFollowing();
  }, []);

  const fetchFollowing = () => {
    fetch(`${CONST.API}/network/following/${auth.pk}`, {
      method: "POST",
    })
      .then((response) => response.json())
      .then((json) => setFollowing(json))
      .catch((error) => {
        console.error(error);
        toast("Error fetching network", { type: "error" });
      });
  };

  const fetchFollowers = () => {
    fetch(`${CONST.API}/network/followers/${auth.pk}`, {
      method: "POST",
    })
      .then((response) => response.json())
      .then((json) => setFollowers(json))
      .catch((error) => {
        console.error(error);
      });
  };

  return (
    <Page title="Network">
      <Tabs fill variant="tabs" defaultActiveKey="followers">
        <Tab
          eventKey="followers"
          title={`Followers (${followers.data?.metadata?.total})`}
          className="mt-4"
        >
          <ListGroup className="mt-3" variant="flush">
            {followers.data?.content.map((element) => (
              <ListGroup.Item key={uuidv4()}>
                <UserItem type="followers" {...element.src} />
              </ListGroup.Item>
            ))}
          </ListGroup>
          {CONST.DEBUG && <pre>{JSON.stringify(followers?.data, null, 2)}</pre>}
        </Tab>
        <Tab
          eventKey="following"
          title={`Following (${following.data?.metadata?.total})`}
          className="mt-4"
        >
          <ListGroup className="mt-3" variant="flush">
            {following.data?.content.map((element) => (
              <ListGroup.Item key={uuidv4()}>
                <UserItem type="following" {...element.dst} />
              </ListGroup.Item>
            ))}
          </ListGroup>
          {CONST.DEBUG && <pre>{JSON.stringify(following?.data, null, 2)}</pre>}
        </Tab>
      </Tabs>
    </Page>
  );
};

const CalendarPage = (props) => {
  const { auth } = useContext(AuthContext);
  const [state, setState] = useState(paginationProps);
  const [semaphore, setSemaphore] = useState(0);

  const slots = { 1: "Morning", 2: "Midday", 3: "Twilight" };

  React.useEffect(() => {
    gofetch();
  }, [semaphore]);

  const gofetch = () => {
    fetch(
      `${CONST.API}/calendar/query?` +
        new URLSearchParams({
          fk: auth.pk,
        }).toString(),
      {
        method: "POST",
        headers: {
          Token: auth.token,
        },
      }
    )
      .then((response) => response.json())
      .then((json) => {
        console.log(json);
        setState(json);
      })
      .catch((error) => {
        console.error(error);
        toast("Failed to fetch calendar", { type: "error" });
      });
  };

  const handleToggle = (date, time, available) => {
    const url = `${CONST.API}/calendar/availability`;
    fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        fk: auth.pk,
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
    <Page title="Calendar" className="text-center">
      <Row className={`mb-2`}>
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
      {state.data.content.map((day) => {
        const date = new Date(day.date);
        const month = date
          .toLocaleString("default", { month: "long" })
          .slice(0, 3);
        const weekday = date
          .toLocaleString("default", { weekday: "long" })
          .slice(0, 3);
        return (
          <Row
            className={`mb-4`}
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
                  onClick={(e) =>
                    handleToggle(
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
      {CONST.DEBUG && <pre>{JSON.stringify(state?.data, null, 2)}</pre>}
    </Page>
  );
};

const SearchPage = (props) => {
  const { auth } = useContext(AuthContext);
  const [state, setState] = useState(null);

  React.useEffect(() => {
    gofetch();
  }, []);

  const gofetch = () => {
    fetch(`${CONST.API}/search`, {
      method: "GET",
      headers: {
        Token: auth.token,
      },
    })
      .then((response) => response.json())
      .then((json) => {
        setState(json);
      })
      .catch((error) => {
        console.error(error);
        toast("Failed to fetch search", { type: "error" });
      });
  };

  return (
    <Page title="Search">
      <pre>{JSON.stringify(state?.data, null, 2)}</pre>
    </Page>
  );
};

const InboxPage = (props) => {
  const { auth } = useContext(AuthContext);
  const [state, setState] = useState(paginationProps);

  const navigate = useNavigate();

  // TODO: semaphore on notifications
  React.useEffect(() => {
    gofetch();
  }, []);

  const gofetch = () => {
    fetch(`${CONST.API}/conversations/${auth.pk}`, {
      method: "GET",
      headers: {
        Token: auth.token,
      },
    })
      .then((response) => response.json())
      .then((json) => {
        setState(json);
      })
      .catch((error) => console.error(error));
  };

  return (
    <Page title="Inbox">
      {state?.data?.content.map((prop) => {
        const ours = auth.pk === prop.src_fk;
        const fk = ours ? prop.dst_fk : prop.src_fk;
        return (
          <InboxItem
            key={uuidv4()}
            ours={ours}
            onClick={() => {
              navigate(ROUTES.CHAT, {
                state: { fk: fk },
              });
            }}
            {...prop}
          />
        );
      })}
      {CONST.DEBUG && <pre>{JSON.stringify(state?.data, null, 2)}</pre>}
    </Page>
  );
};

const DefaultPage = (props) => {
  const navigate = useNavigate();

  return (
    <Page>
      <main style={{ padding: "1rem" }}>
        <p>There's nothing here!</p>
        <Button variant="secondary" onClick={() => navigate(-1)}>
          Go Back
        </Button>
        <Button
          variant="primary"
          onClick={() => navigate(ROUTES.HOME, { replace: true })}
        >
          Go Home
        </Button>
      </main>
    </Page>
  );
};

const ChatPage = (props) => {
  const { auth } = useContext(AuthContext);
  const [state, setState] = useState({
    ...paginationProps,
    context: { dst: null, src: null },
  });
  const location = useLocation();
  const { fk } = location.state;
  const { pk } = auth;

  console.log(pk, fk);
  // show username in navbar

  React.useEffect(() => {
    window.scrollTo(0, document.body.scrollHeight);
  }, [state]);

  React.useEffect(() => {
    gofetch(pk, fk);
  }, []);

  const gofetch = (src, dst) => {
    console.log(`Loading chat with ${src} and ${dst}`);
    fetch(`${CONST.API}/conversations/${src}/${dst}`, {
      method: "GET",
      headers: {
        Token: auth.token,
      },
    })
      .then((response) => response.json())
      .then((json) => {
        console.log(json);
        setState(json);
      })
      .catch((error) => {
        console.error(error);
        toast("Failed to fetch chat", { type: "error" });
      });
  };

  const sendChat = (src, dst, body) => {
    console.log(`Sending message from ${src} to ${dst}: ${body}`);
    fetch(`${CONST.API}/messages`, {
      method: "POST",
      headers: {
        Token: auth.token,
      },
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        src_fk: src,
        dst_fk: dst,
        body: body,
      }),
    })
      .then((response) => response.json())
      .then((json) => {
        gofetch(src, dst);
      })
      .catch((error) => {
        console.error(error);
        toast("Failed to send chat", { type: "error" });
      });
  };

  const WelcomeMessage = () => {
    return (
      <div
        className="text-center text-muted"
        style={{
          fontSize: "small",
          marginBottom: "0.5rem",
        }}
      >
        Start of your conversation
      </div>
    );
  };

  // get latest message sent by each party and show a timestamp for context
  const includeTimestampsFor = [
    state.data?.content.find((element) => element.dst_fk === pk)?.pk,
    state.data?.content.find((element) => element.src_fk === pk)?.pk,
  ].filter((e) => e);

  console.log(state);

  return (
    <Page title={`Chat with ${fk}`}>
      {state.data?.metadata.page === state.data?.metadata.pages && (
        <WelcomeMessage />
      )}
      {[...(state.data?.content || [])].reverse().map((prop, i, row) => (
        <ChatBubble
          key={uuidv4()}
          ours={prop.src_fk === pk}
          timestamp={includeTimestampsFor.includes(prop.pk)}
          {...prop}
        />
      ))}
      {/* Account for the input field pinned to bottom */}
      <div
        style={{
          height: "6rem",
        }}
      ></div>
      <ChatInput onSubmit={(body) => sendChat(pk, fk, body)} />
      {/* <pre>{JSON.stringify(state.data, null, 2)}</pre> */}
    </Page>
  );
};

const SharePage = (props) => {
  const { auth } = useContext(AuthContext);
  const [state, setState] = useState(requestProps);

  React.useEffect(() => {
    gofetch();
  }, []);

  const gofetch = () => {
    fetch(`${CONST.API}/users/${auth.pk}`, {
      method: "GET",
      headers: {
        Token: auth.token,
      },
    })
      .then((response) => response.json())
      .then((json) => {
        setState(json);
      })
      .catch((error) => {
        console.error(error);
        toast("Failed to fetch share", { type: "error" });
      });
  };

  const href = `https://whoseaway.com/qr/${auth.pk}`;

  return (
    <Page title="Share">
      <Row className="pt-4">
        <Col className="text-center">
          <h2>@{state.data?.username}</h2>
          <QRCode value={href} />
          <div className="pt-4">Scan the code using your smartphone camera</div>
        </Col>
      </Row>
      {CONST.DEBUG && <pre>{JSON.stringify(state?.data, null, 2)}</pre>}
    </Page>
  );
};

const SettingsPage = (props) => {
  const { auth } = useContext(AuthContext);
  const [state, setState] = useState(requestProps);

  React.useEffect(() => {
    gofetch();
  }, []);

  const gofetch = () => {
    fetch(`${CONST.API}/users/${auth.pk}`, {
      method: "GET",
      headers: {
        Token: auth.token,
      },
    })
      .then((response) => response.json())
      .then((json) => {
        setState(json);
      })
      .catch((error) => {
        console.error(error);
        toast("Failed to fetch settings", { type: "error" });
      });
  };

  // nested models
  const { profile, image, location } = state?.data || {};
  // identify
  const { pk, username, created_at } = state?.data || {};

  return (
    <Page title="Settings">
      <Tabs fill variant="tabs" defaultActiveKey="profile">
        <Tab eventKey="profile" title={`Profile`} className="mt-4">
          <pre>{JSON.stringify(profile, null, 2)}</pre>
        </Tab>
        <Tab eventKey="image" title={`Image`} className="mt-4">
          <pre>{JSON.stringify(image, null, 2)}</pre>
        </Tab>
        <Tab eventKey="location" title={`Location`} className="mt-4">
          <pre>{JSON.stringify(location, null, 2)}</pre>
        </Tab>
        <Tab eventKey="Account" title={`Account`} className="mt-4">
          <pre>{JSON.stringify({ pk, username, created_at }, null, 2)}</pre>
        </Tab>
      </Tabs>
      {CONST.DEBUG && <pre>{JSON.stringify(state?.data, null, 2)}</pre>}
    </Page>
  );
};

const ProtectedRoute = ({ redirectPath = "/", children }) => {
  const { isAuthed } = useContext(AuthContext);

  if (!isAuthed()) {
    return <Navigate to={redirectPath} replace />;
  }

  return children ? children : <Outlet />;
};

const App = () => {
  const { auth, setAuth, resetAuth, isAuthed } = useAuth();

  return (
    <>
      <AuthContext.Provider value={{ auth, setAuth, resetAuth, isAuthed }}>
        <ToastContainer autoClose={1500} newestOnTop={true} />
        <BrowserRouter>
          <Routes>
            <Route path={`${ROUTES.HOME}`} element={<HomePage />} />
            <Route element={<ProtectedRoute auth={auth} />}>
              <Route path={`${ROUTES.TIMELINE}`} element={<TimelinePage />} />
              <Route path={`${ROUTES.USER}/:pk`} element={<UserPage />} />
              <Route path={`${ROUTES.NETWORK}`} element={<NetworkPage />} />
              <Route path={`${ROUTES.CALENDAR}`} element={<CalendarPage />} />
              <Route path={`${ROUTES.SEARCH}`} element={<SearchPage />} />
              <Route path={`${ROUTES.INBOX}`} element={<InboxPage />} />
              <Route path={`${ROUTES.CHAT}`} element={<ChatPage />} />
              <Route path={`${ROUTES.SETTINGS}`} element={<SettingsPage />} />
              <Route path={`${ROUTES.SHARE}`} element={<SharePage />} />
            </Route>
            <Route path="*" element={<DefaultPage />} />
          </Routes>
        </BrowserRouter>
      </AuthContext.Provider>
    </>
  );
};

export default App;

/**
 * Default Props
 */
Page.defaultProps = {
  title: null,
};

Navigation.defaultProps = {
  brand: {
    text: "Whose ⛳️ Away",
    type: "title",
  },
};

CalendarPage.defaultProps = {
  data: {
    content: [],
    metadata: {},
  },
  error: null,
  status: 200,
  timestamp: 1649515010927,
};

CalendarTray.defaultProps = {
  content: [
    { pk: 1, fk: 1, date: "2022-04-11", time: 2 },
    { pk: 2, fk: 1, date: "2022-04-11", time: 1 },
    { pk: 3, fk: 1, date: "2022-04-15", time: 1 },
  ],
};
