import React, { useState, useContext, createContext } from "react";
import {
  BrowserRouter,
  Route,
  Routes,
  Link,
  Navigate,
  Outlet,
  useNavigate,
} from "react-router-dom";
import { v4 as uuidv4 } from "uuid";
import "bootstrap/dist/css/bootstrap.min.css";
import "./App.css";

const CONST = {
  API: `http://192.168.1.114:4000`,
};

const ROUTES = {
  INDEX: "/",
  TIMELINE: "/timeline",
  USER: "/user",
  NETWORK: "/network",
  CALENDAR: "/calendar",
  SEARCH: "/search",
  INBOX: "/inbox",
  CHAT: "/chat",
};

/**
 * AuthContext: initialized using session storage, creates a provider
 * Pages take in the AuthContext in order to fetch the correct data, using local state
 * If authentication is not present, pages show no presentation except for a banner
 *
 *
 */

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
    saveAuth({});
  };

  return {
    auth,
    setAuth: saveAuth,
    resetAuth: clearAuth,
    isAuthed: () => !!auth?.pk || !!auth?.token, // FIXME
  };
};

const Nav = (props) => {
  return (
    <nav>
      <ul>
        {Object.entries(ROUTES).map(([key, val]) => (
          <li>
            <Link key={uuidv4()} to={val}>
              {key}
            </Link>
          </li>
        ))}
      </ul>
    </nav>
  );
};

const IndexPage = (props) => {
  const { setAuth, resetAuth, isAuthed } = useContext(AuthContext);

  const navigate = useNavigate();

  const handleLogin = (e) => {
    e.preventDefault();
    fetch(`${CONST.API}/auth/login`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        username: e.target?.username?.value,
        password: e.target?.password?.value,
      }),
    })
      .then((response) => response.json())
      .then((json) => {
        setAuth(json.data);
        navigate(ROUTES.TIMELINE, { replace: true });
      })
      .catch((error) => console.error(error));
  };

  return (
    <>
      {isAuthed() && <Nav />}
      <h1>Login</h1>
      <pre>Authorized: {JSON.stringify(isAuthed())}</pre>
      <form onSubmit={handleLogin}>
        <input
          type="text"
          id="username"
          placeholder="username"
          value="alice"
          required
        />
        <input
          type="password"
          id="password"
          placeholder="password"
          value="alice"
          required
        />
        <button type="submit">Log In</button>
      </form>
      <button onClick={resetAuth}>Log Out</button>
    </>
  );
};

const TimelinePage = (props) => {
  const { auth, isAuthed } = useContext(AuthContext);
  const title = "Timeline Page";
  return (
    <div>
      <Nav />
      <h1>{isAuthed() ? title : "Unauthorized"}</h1>
      <pre>Authorized: {JSON.stringify(isAuthed())}</pre>
    </div>
  );
};

const UserPage = (props) => {
  const { auth, isAuthed } = useContext(AuthContext);
  const [state, setState] = useState(null);
  const title = "User Page";

  React.useEffect(() => {
    doFetch();
  }, []);

  const doFetch = () => {
    fetch(`${CONST.API}/users/${auth.pk}`, {
      method: "GET",
    })
      .then((response) => response.json())
      .then((json) => setState(json))
      .catch((error) => console.error(error));
  };

  console.log(state);
  return (
    <div>
      <Nav />
      <h1>{isAuthed() ? title : "Unauthorized"}</h1>
      <blockquote className="bg-danger bordered">{state?.error}</blockquote>
      <pre>Authorized: {JSON.stringify(isAuthed())}</pre>
      <pre>{JSON.stringify(state?.data, null, 2)}</pre>
    </div>
  );
};

const NetworkPage = (props) => {
  return (
    <div>
      <Nav />
      <h1>Network</h1>
    </div>
  );
};

const CalendarPage = (props) => {
  return (
    <div>
      <Nav />
      <h1>Calendar</h1>
    </div>
  );
};

const SearchPage = (props) => {
  return (
    <div>
      <Nav />
      <h1>Search</h1>
    </div>
  );
};

const InboxPage = (props) => {
  const { auth } = useContext(AuthContext);
  const [state, setState] = useState(null);

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
    <div>
      <Nav />
      <h1>Inbox</h1>
      <pre>{JSON.stringify(state?.data, null, 2)}</pre>
    </div>
  );
};

const ChatPage = (props) => {
  const { auth } = useContext(AuthContext);
  const [state, setState] = useState(null);

  React.useEffect(() => {
    gofetch();
  }, []);

  const gofetch = () => {
    fetch(`${CONST.API}/conversations/${auth.pk}/${2}`, {
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
    <div>
      <Nav />
      <h1>Chat</h1>
      <pre>{JSON.stringify(state?.data, null, 2)}</pre>
    </div>
  );
};

const DefaultPage = (props) => {
  return (
    <main style={{ padding: "1rem" }}>
      <p>There's nothing here!</p>
    </main>
  );
};

const ProtectedRoute = ({ redirectPath = "/", children }) => {
  const { isAuthed } = useContext(AuthContext);

  if (!isAuthed()) {
    return <Navigate to={redirectPath} replace />;
  }

  return children ? children : <Outlet />;
};

// intentionally separate
const AuthContext = createContext();
//

const App = () => {
  const { auth, setAuth, resetAuth, isAuthed } = useAuth();

  console.log(`auth:`, auth);
  console.log(`authorized`, isAuthed());

  return (
    <>
      <AuthContext.Provider value={{ auth, setAuth, resetAuth, isAuthed }}>
        {/* <pre>{JSON.stringify(auth, null, 2)}</pre> */}
        <BrowserRouter>
          <Routes>
            <Route path="/" element={<IndexPage />} />
            <Route element={<ProtectedRoute auth={auth} />}>
              <Route path="timeline" element={<TimelinePage />} />
              <Route path="user" element={<UserPage />} />
              <Route path="network" element={<NetworkPage />} />
              <Route path="calendar" element={<CalendarPage />} />
              <Route path="search" element={<SearchPage />} />
              <Route path="inbox" element={<InboxPage />} />
              <Route path="chat" element={<ChatPage />} />
            </Route>
            <Route path="*" element={<DefaultPage />} />
          </Routes>
        </BrowserRouter>
      </AuthContext.Provider>
    </>
  );
};

export default App;
