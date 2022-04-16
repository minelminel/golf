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
import { AiFillCar } from "react-icons/ai";
import { BiDrink, BiCopy } from "react-icons/bi";
import { BsFillCalendarCheckFill } from "react-icons/bs";
import { FaBeer, FaWalking, FaCoffee } from "react-icons/fa";
import { MdClear } from "react-icons/md";
import { RiUserSharedFill } from "react-icons/ri";
import { SiHandshake } from "react-icons/si";
import {
  TiWeatherPartlySunny,
  TiWeatherSunny,
  TiWeatherShower,
} from "react-icons/ti";
// END ICONS

import { v4 as uuidv4 } from "uuid";
import { ToastContainer, toast } from "react-toastify";
import QRCode from "react-qr-code";
import {
  MapContainer,
  Marker,
  Popup,
  TileLayer,
  Pane,
  Circle,
} from "react-leaflet";
import { useForm } from "react-hook-form";

import { formatTimeSince } from "./utils";

import "react-toastify/dist/ReactToastify.css";
import "bootstrap/dist/css/bootstrap.min.css";
import "leaflet/dist/leaflet.css";
import "./App.css";

import Logo from "./static/logo.png";

const CONST = {
  API: `http://192.168.1.114:4000/api`,
  DEBUG: false,
};
console.warn(`DEBUG MODE ENABLED: ${CONST.DEBUG}`);

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
    const creds = {
      email: email?.value,
      username: username?.value,
      password: password?.value,
    };
    console.log(creds);
    handleSubmit(creds);
  };

  return loggedIn ? (
    <BannerBlock
      bg="info"
      text={loggedIn ? "It looks like you're already logged in" : byline}
    />
  ) : (
    <Form onSubmit={onSubmit} id="register">
      <fieldset>
        <Form.Group>
          <InputGroup className="mb-3 shadow">
            <InputGroup.Text>@</InputGroup.Text>
            <FormControl
              placeholder="Username"
              id="username"
              required
              value={`michael`}
            />
          </InputGroup>
        </Form.Group>
        <Form.Group className="mb-3">
          <Form.Label>Email address</Form.Label>
          <Form.Control
            className="mb-2 shadow"
            type="email"
            placeholder="Enter email"
            id="email"
            required
            value={`michael@mail.com`}
          />
          <Form.Text className="text-muted">No spam, we promise</Form.Text>
        </Form.Group>

        <Form.Group className="mb-4">
          <Form.Label>Password</Form.Label>
          <Form.Control
            className="shadow"
            type="password"
            placeholder="Password"
            id="password"
            required
            value={`michael`}
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
    const creds = { username: username?.value, password: password?.value };
    handleSubmit(creds);
  };

  return loggedIn ? (
    <BannerBlock
      bg="info"
      text={loggedIn ? "It looks like you're already logged in" : byline}
    />
  ) : (
    <Form onSubmit={onSubmit} id="login">
      <fieldset>
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
      <div className="ms-3 me-auto truncate">
        <div className="align-middle">
          <strong>@{ours ? dst?.username : src?.username}</strong>
          &nbsp;
          {ours && !read ? "🔵" : null}
        </div>
        <p
          style={{
            lineBreak: "nowrap",
            overflow: "hidden",
            textOverflow: "ellipsis",
            wordWrap: "break-word",
            maxWidth: "16rem",
          }}
        >
          {ours ? `You: ` : ``}
          {body}
        </p>
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
    clear();
  };

  const clear = (e) => {
    setInput(``);
  };

  const fontSize = "2rem";

  return (
    <Container>
      <Row
        className="fixed-bottom text-center"
        style={{
          margin: "0 auto",
          backgroundColor: "var(--bs-dark)",
          height: "6rem",
        }}
      >
        <Col
          xs
          sm={10}
          md={7}
          lg={6}
          xl={4}
          style={{
            margin: "0 auto",
            lineHeight: fontSize,
          }}
        >
          <Button
            className="shadow"
            variant="outline-secondary"
            disabled={input.length < 1}
            onClick={clear}
            style={{
              borderRadius: "8px",
              marginRight: "1rem",
              lineHeight: fontSize,
            }}
            title="Clear"
          >
            <MdClear size={20} />
          </Button>
          <input
            onChange={type}
            value={input}
            as="textarea"
            rows={2}
            placeholder="Start typing..."
            style={{
              padding: "5px",
              margin: "3px",
              borderRadius: "8px",
              border: "1px solid gray",
              width: "70%",
              marginTop: "0.5rem",
            }}
          />
          <Button
            className="shadow"
            disabled={input.length < 1}
            onClick={send}
            style={{
              borderRadius: "8px",
              marginLeft: "1rem",
              lineHeight: fontSize,
            }}
            title="Send"
          >
            <Send size={20} />
          </Button>
        </Col>
      </Row>
    </Container>
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
        // console.log(date, available);
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
  // const { profile = {} } = props;
  const { mobility, drinking, weather } = props;
  return (
    <Row
      className="text-center mb-4"
      style={{
        color: "#64D3D6",
      }}
    >
      {/* {Object.entries({ mobility, drinking, weather })
        .filter(([key, value]) => value)
        .map(([key, value]) => {
          return (
            <Col>
              {ENUMS}[key][value]
              <div
                className="mt-2"
                style={{ color: "var(--bs-light)", fontSize: "0.85rem" }}
              >
                {DESCRIPTIONS[key][value]}
              </div>
            </Col>
          );
        })} */}
      <Col>
        {ENUMS.mobility[mobility]}
        <div
          className="mt-2"
          style={{ color: "var(--bs-light)", fontSize: "0.85rem" }}
        >
          {DESCRIPTIONS.mobility[mobility]}
        </div>
      </Col>
      <Col>
        {ENUMS.drinking[drinking]}
        <div
          className="mt-2"
          style={{ color: "var(--bs-light)", fontSize: "0.85rem" }}
        >
          {DESCRIPTIONS.drinking[drinking]}
        </div>
      </Col>
      <Col>
        {ENUMS.weather[weather]}
        <div
          className="mt-2"
          style={{ color: "var(--bs-light)", fontSize: "0.85rem" }}
        >
          {DESCRIPTIONS.weather[weather]}
        </div>
      </Col>
    </Row>
  );
};

const UserItem = (props) => {
  // TODO: handle action as atom component
  const {
    type, // row,card
    actionProps = {},
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

  const action = (
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
        bg={actionProps.variant}
        text={actionProps.variant === "light" ? "dark" : "light"}
        style={{ ...(actionProps.onClick ? { cursor: "pointer" } : {}) }}
        onClick={actionProps.onClick}
      >
        {actionProps.text}
      </Badge>
    </div>
  );

  const href = `${ROUTES.USER}/${pk}`;

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
                alt={`@${username}`}
                title={`@${username}`}
                onClick={onClick}
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
                <span className="fw-bold">{profile.alias}&nbsp;</span>
                <a href={href}>@{username}</a>
              </span>
            </Row>
            <Row>
              <small className="px-0 text-muted">{location.label}</small>
            </Row>
            <Row>{profile.bio}</Row>
          </Col>
          <Col className="col-2">{action}</Col>
        </Row>
        {type === "card" && (
          <Row>
            <Col className="px-0 mt-1">
              <CalendarTray content={calendar} />
            </Col>
          </Row>
        )}
      </Container>
    </ListGroup.Item>
  );
};

const MapPanel = (props) => {
  const { distance, label, geometry = {} } = props;
  const { coordinates = [] } = geometry;
  const position = coordinates.slice().reverse();
  // TODO: consider distance & label

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

const useRequest = (auth) => {
  const { token } = auth;

  async function doRequest(url, { method = "GET", json, params }) {
    const headers = {
      ...(token ? { Token: token } : {}),
      ...(json ? { "Content-Type": "application/json" } : {}),
    };

    const kwargs = {
      method,
      headers,
      mode: "cors",
      cache: "no-cache",
      credentials: "same-origin",
      ...(json ? { body: JSON.stringify(json) } : {}),
    };

    console.debug(`useRequest:`, url, kwargs, headers);

    const response = await fetch(
      params ? `${url}?${new URLSearchParams(params).toString()}` : url,
      kwargs
    );

    return response;
  }

  return doRequest;
};

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
  const request = useRequest(auth);

  const [notifications, setNotifications] = useState();
  const navigate = useNavigate();
  const { brand } = props;

  const iconSize = 28;

  React.useEffect(() => {
    isAuthed() && gofetch();
  }, []);

  const gofetch = () => {
    request(`${CONST.API}/notifications/${auth.pk}`, {
      method: "POST",
    })
      .then((response) => response.json())
      .then((json) => {
        console.log(json);
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
            <NavDropdown title={<Layers size={iconSize} />}>
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
              <NavDropdown.Item onClick={() => navigate(ROUTES.SHARE)}>
                Share&nbsp;
                <Share size={18} />
              </NavDropdown.Item>
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
            <Navbar.Brand className="mx-0" href="/">
              {brand.text}
            </Navbar.Brand>
          ) : (
            <Navbar.Text className="text-muted small">{brand.text}</Navbar.Text>
          )}
          {/* RIGHT */}
          {isAuthed() ? (
            <Nav.Link>
              <Link to={ROUTES.INBOX}>
                <Box size={iconSize} />
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
            style={{
              margin: "0 auto",
            }}
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
  const { auth, setAuth, isAuthed } = useContext(AuthContext);

  const navigate = useNavigate();
  const request = useRequest(auth);

  const handleRegister = (creds) => {
    request(`${CONST.API}/auth/register`, {
      method: "POST",
      json: creds,
    })
      .then((response) => response.json())
      .then((json) => {
        if (json.error) {
          throw new Error(json.error);
        }
        // TODO: redirect here to "quickstart" workflow
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
    request(`${CONST.API}/auth/login`, {
      method: "POST",
      json: creds,
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
            // onSelect={() => {
            //   // allow tab change to propagate before checking resize
            //   setTimeout(() => {
            //     window.scrollTo(0, document.body.scrollHeight);
            //   }, 25);
            // }}
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
        <Col>
          {state?.data?.content ? (
            state.data.content.map((element) => element)
          ) : (
            <div>Nothing to display</div>
          )}
        </Col>
      </Row>
    </Page>
  );
};

const UserPage = (props) => {
  const { auth, isAuthed } = useContext(AuthContext);
  const [state, setState] = useState(requestProps);
  const { pk } = useParams();

  const navigate = useNavigate();
  const request = useRequest(auth);

  const between = "1rem";

  React.useEffect(() => {
    gofetch();
  }, [pk]);

  const gofetch = () => {
    request(`${CONST.API}/users/${pk}`, {
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
                  {state.data?.profile?.handicap}
                </span>
              </Col>
            </Row>
            <PreferenceTray {...(state.data?.profile || {})} />
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
            }}
          >
            <MapPanel {...(state.data?.location || {})} />
          </div>
        </Col>
      </Row>
      {CONST.DEBUG && <pre>{JSON.stringify(state?.data, null, 2)}</pre>}
    </Page>
  );
};

const NetworkPage = (props) => {
  const { auth } = useContext(AuthContext);
  const request = useRequest(auth);

  const [semaphore, setSemaphore] = useState(0);
  const [followers, setFollowers] = useState(paginationProps);
  const [following, setFollowing] = useState(paginationProps);

  React.useEffect(() => {
    fetchFollowers();
    fetchFollowing();
  }, [semaphore]);

  const fetchFollowing = () => {
    request(`${CONST.API}/network/following/${auth.pk}`, {
      method: "POST",
    })
      .then((response) => response.json())
      .then((json) => setFollowing(json))
      .catch((error) => {
        console.error(error);
        toast("Error fetching following", { type: "error" });
      });
  };

  const fetchFollowers = () => {
    request(`${CONST.API}/network/followers/${auth.pk}`, {
      method: "POST",
    })
      .then((response) => response.json())
      .then((json) => setFollowers(json))
      .catch((error) => {
        console.error(error);
        toast(`Error fetching followers`, { type: "error" });
      });
  };

  const follow = (src_fk, dst_fk) => {
    request(`${CONST.API}/network/follow`, {
      method: "POST",
      json: {
        src_fk,
        dst_fk,
      },
    })
      .then((response) => response.json())
      .then((json) => {
        console.log(json);
        toast(`Followed`);
        setSemaphore(semaphore + 1);
      })
      .catch((error) => {
        console.error(error);
        toast(`Error following`, { type: "error" });
      });
  };

  const unfollow = (src_fk, dst_fk) => {
    request(`${CONST.API}/network/unfollow`, {
      method: "POST",
      json: {
        src_fk,
        dst_fk,
      },
    })
      .then((response) => response.json())
      .then((json) => {
        console.log(json);
        toast(`Unfollowed`);
        setSemaphore(semaphore + 1);
      })
      .catch((error) => {
        console.error(error);
        toast(`Error unfollowing`, { type: "error" });
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
            {followers.data?.content.map((element) => {
              const action = element?.network?.reciprocal
                ? {
                    text: <SiHandshake size={18} />,
                    variant: "dark",
                  }
                : {
                    text: "Follow",
                    variant: "success",
                    onClick: () => {
                      follow(auth.pk, element.src_fk);
                    },
                  };
              return (
                <ListGroup.Item key={uuidv4()}>
                  <UserItem type="row" {...element.src} actionProps={action} />
                </ListGroup.Item>
              );
            })}
          </ListGroup>
          {CONST.DEBUG && <pre>{JSON.stringify(followers?.data, null, 2)}</pre>}
        </Tab>
        <Tab
          eventKey="following"
          title={`Following (${following.data?.metadata?.total})`}
          className="mt-4"
        >
          <ListGroup className="mt-3" variant="flush">
            {following.data?.content.map((element) => {
              const action = {
                text: "Unfollow",
                variant: "primary",
                onClick: () => {
                  unfollow(auth.pk, element.dst_fk);
                },
              };
              return (
                <ListGroup.Item key={uuidv4()}>
                  <UserItem type="row" {...element.dst} actionProps={action} />
                </ListGroup.Item>
              );
            })}
          </ListGroup>
          {CONST.DEBUG && <pre>{JSON.stringify(following?.data, null, 2)}</pre>}
        </Tab>
      </Tabs>
    </Page>
  );
};

const CalendarPage = (props) => {
  const { auth } = useContext(AuthContext);
  const request = useRequest(auth);

  const [state, setState] = useState(paginationProps);
  const [semaphore, setSemaphore] = useState(0);

  const slots = { 1: "Morning", 2: "Midday", 3: "Twilight" };

  React.useEffect(() => {
    gofetch();
  }, [semaphore]);

  const gofetch = () => {
    request(`${CONST.API}/calendar/query`, {
      method: "POST",
      params: {
        fk: auth.pk,
      },
    })
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
    request(url, {
      method: "POST",
      json: {
        fk: auth.pk,
        date: date,
        time: time,
        available: available,
      },
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
  // TODO: pass search props to higher-level component to
  // preserve the state of the form when navigating back.
  const { auth } = useContext(AuthContext);
  const request = useRequest(auth);

  const [state, setState] = useState(requestProps);
  const [query, setQuery] = useState(``); // username

  const navigate = useNavigate();

  React.useEffect(() => {
    // no-op
  }, []);

  const handleInput = (event) => {
    const name = event.target.value;
    setQuery(name);
    name.length > 0 && handleQuery({ username: name, alias: name });
  };

  const handleQuery = (params) => {
    request(`${CONST.API}/search/query`, { method: "POST", json: params })
      .then((response) => response.json())
      .then((json) => {
        console.log(json);
        setState(json);
      })
      .catch((error) => {
        console.error(error);
        setState({ error });
        toast("Failed to fetch search", { type: "error" });
      });
  };

  return (
    <Page title="Search">
      <Row>
        <Col className="mt-4" style={{ margin: "0 auto" }}>
          <InputGroup className="mb-3">
            <InputGroup.Text>@</InputGroup.Text>
            <FormControl
              placeholder="Name or username"
              value={query}
              onInput={handleInput}
            />
          </InputGroup>
        </Col>
      </Row>
      <Row>
        <Col>
          {query && !state.data?.metadata?.total && (
            <small className="text-muted">No results</small>
          )}
          {/* Pagination-first component */}
          <ListGroup className="mt-3" variant="flush">
            {query &&
              state.data?.content.map(
                (element) =>
                  element.pk !== auth.pk && (
                    <ListGroup.Item key={uuidv4()}>
                      <UserItem
                        type="card"
                        {...element}
                        actionProps={{
                          text: <RiUserSharedFill size={24} />,
                          variant: "light",
                          onClick: () => {
                            navigate(`${ROUTES.USER}/${element.pk}`);
                          },
                        }}
                      />
                    </ListGroup.Item>
                  )
              )}
            {/* PAGINATION LINKS */}
            {state?.data?.metadata?.links?.next && (
              <ListGroup.Item key={uuidv4()}>
                <div className="my-3 text-center">
                  <a href="">Next Page</a>
                </div>
              </ListGroup.Item>
            )}
          </ListGroup>
        </Col>
      </Row>

      {CONST.DEBUG && <pre>{JSON.stringify(state.data, null, 2)}</pre>}
    </Page>
  );
};

const InboxPage = (props) => {
  const { auth } = useContext(AuthContext);
  const request = useRequest(auth);
  const [state, setState] = useState(paginationProps);

  const navigate = useNavigate();

  // TODO: semaphore on notifications
  React.useEffect(() => {
    gofetch();
  }, []);

  const gofetch = () => {
    request(`${CONST.API}/conversations/${auth.pk}`, {
      method: "GET",
    })
      .then((response) => response.json())
      .then((json) => {
        setState(json);
      })
      .catch((error) => console.error(error));
  };

  const acknowledgeNotification = () => {
    console.log(`ackNot`);
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
              // acknowledgeNotification({ src_fk: auth.pk, dst_fk: });
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
  const request = useRequest(auth);

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
    request(`${CONST.API}/conversations/${src}/${dst}`, {
      method: "GET",
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
    request(`${CONST.API}/messages`, {
      method: "POST",
      json: {
        src_fk: src,
        dst_fk: dst,
        body: body,
      },
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

  const href = `https://whoseaway.com/ref/${auth.pk}`;

  return (
    <Page title="Share">
      <Row className="pt-4">
        <Col className="text-center">
          <h2 className="pb-2">@{state.data?.username}</h2>
          <QRCode value={href} />
          <div className="pt-4">Scan the code using your smartphone camera</div>
        </Col>
      </Row>
      <hr />
      <Row className="pt-4">
        <Col className="text-center d-grid">
          <div className="pb-4">Or click below to copy the link</div>
          <Button
            style={{
              width: "80%",
              margin: "0 auto",
            }}
            className="shadow"
            onClick={() => {
              console.log("copy to clipboard");
              navigator.clipboard
                .writeText(href)
                .then(() => {
                  console.log(`Copied to clipboard`);
                  toast(`Copied to clipboard`, { type: "success" });
                })
                .catch((error) => {
                  console.error(`Failed to copy to clipboard`);
                });
            }}
          >
            <BiCopy size={24} />
          </Button>
          <h4 className="py-4">
            <a href={href}>{href}</a>
          </h4>
        </Col>
      </Row>
      {CONST.DEBUG && <pre>{JSON.stringify(state?.data, null, 2)}</pre>}
    </Page>
  );
};

const SettingsPage = (props) => {
  const { auth } = useContext(AuthContext);
  const [state, setState] = useState(requestProps);

  const request = useRequest(auth);

  React.useEffect(() => {
    gofetch();
  }, []);

  const gofetch = () => {
    request(`${CONST.API}/users/${auth.pk}`, {
      method: "GET",
    })
      .then((response) => response.json())
      .then((json) => {
        console.log(json);
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
        {/* PROFILE */}
        <Tab eventKey="profile" title={`Profile`} className="mt-4">
          {["alias", "bio", "handicap", "mobility", "drinking", "weather"].map(
            (field) => {
              const value = profile ? profile[field] : null;
              return (
                <Form.Group key={uuidv4()}>
                  <Form.Label>{field}</Form.Label>
                  <Form.Control type="text" placeholder={value} />
                </Form.Group>
              );
            }
          )}
          {CONST.DEBUG && <pre>{JSON.stringify(profile, null, 2)}</pre>}
        </Tab>
        {/* IMAGE */}
        <Tab eventKey="image" title={`Image`} className="mt-4">
          <Form.Group controlId="formFile" className="mb-3">
            <Form.Label>Default file input example</Form.Label>
            <Form.Control type="file" />
          </Form.Group>
          {CONST.DEBUG && <pre>{JSON.stringify(image, null, 2)}</pre>}
        </Tab>
        {/* LOCATION */}
        <Tab eventKey="location" title={`Location`} className="mt-4">
          <Form.Group controlId="location.label" className="mb-3">
            <Form.Label>Default text input example</Form.Label>
            <Form.Control type="text" placeholder="label" />
          </Form.Group>
          <Form.Group controlId="location.geometry" className="mb-3">
            <Form.Label>Default text input example</Form.Label>
            <Form.Control type="text" placeholder="geometry" />
          </Form.Group>
          <div
            style={{
              marginTop: "3rem",
              height: "10rem",
            }}
          >
            <MapPanel {...location} />
          </div>
          {CONST.DEBUG && <pre>{JSON.stringify(location, null, 2)}</pre>}
        </Tab>
        {/* ACCOUNT */}
        <Tab eventKey="Account" title={`Account`} className="mt-4">
          <Form.Group controlId="user.email" className="mb-3">
            <Form.Label>Default text input example</Form.Label>
            <Form.Control type="text" placeholder="email" />
          </Form.Group>
          <Form.Group controlId="user.pk" className="mb-3">
            <Form.Label>Default text input example</Form.Label>
            <Form.Control type="text" placeholder="pk" />
          </Form.Group>
          <Form.Group controlId="user.username" className="mb-3">
            <Form.Label>Default text input example</Form.Label>
            <Form.Control type="text" placeholder="username" />
          </Form.Group>
          <Form.Group controlId="user.created_at" className="mb-3">
            <Form.Label>Default text input example</Form.Label>
            <Form.Control type="text" placeholder="created_at" />
          </Form.Group>
          {CONST.DEBUG && (
            <pre>{JSON.stringify({ pk, username, created_at }, null, 2)}</pre>
          )}
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
        <ToastContainer autoClose={100} newestOnTop={true} />
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
    text: <img src={Logo} height={48} />,
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
