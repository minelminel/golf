import React from "react";
import { Routes, Route, Link, useParams } from "react-router-dom";
import "./App.css";

import { ROUTES } from "./constants";

const App = () => {
  const Default = (props) => {
    const { as } = props;
    const params = useParams();
    console.log(params);
    return <div>Page: {as}</div>;
  };
  return (
    <div className="App">
      <h1>Welcome to React Router!</h1>
      <ul>
        {Object.entries(ROUTES).map(([key, value]) => (
          <li>
            <Link to={value}>{key}</Link>
          </li>
        ))}
      </ul>
      <Routes>
        {Object.entries(ROUTES).map(([key, value]) => (
          <Route path={value} element={<Default as={key} />} />
        ))}
      </Routes>
    </div>
  );
};

export default App;
