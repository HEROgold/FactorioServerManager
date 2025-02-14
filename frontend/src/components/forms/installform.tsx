import React, { useState } from "react";
import {
  FormField,
  FormHandler,
  FormSelector,
  FormSubmit,
} from "./formHandler.tsx";
import { ENDPOINTS } from "../../constants.ts";

export type InstallFormProps = {
  name: string;
  version: [number, number, number];
  port: number;
};

export default function InstallForm() {
  const serverName = "FactorioServer";

  // const nameField = new FormField('name', serverName, 'text');
  // const formHandler = new FormHandler('post', ENDPOINTS.InstallServer, [
  //     nameField,
  //     new FormSelector('version', [1, 0, 0], 'text'),
  //     new FormField('port', 34197, 'number'),
  //     new FormSubmit(),
  // ]);
  // formHandler.linkAction(nameField);

  // return formHandler.render()

  // Original code:
  // const changeHandler = (e: React.ChangeEvent<HTMLInputElement>) => setProps({...props, [e.target.name]: e.target.value});
  // return (
  //     <form method="post" action={ENDPOINTS.InstallServer(props.name)}>
  //         <label>{props.name}</label>
  //         <input type="text" name="name" value={props.name} onChange={changeHandler} />
  //         <br />
  //         <label>{props.version.join('.')}</label>
  //         <input type="number" name="version" value={props.version.join('.')} onChange={changeHandler} />
  //         <br />
  //         <label>{props.port}</label>
  //         <input type="number" name="port" value={props.port} onChange={changeHandler} />
  //         <button type="submit">Submit</button>
  //     </form>
  // );
  const [name, setName] = useState(serverName);
  const [version, setVersion] = useState("2.0.0");
  const [port, setPort] = useState(34197);
  let availableVersions;
  fetch(ENDPOINTS.FactorioVersions).then((res) =>
    res.json().then((data) => (availableVersions = data))
  );

  return (
    <form method="post" action={ENDPOINTS.InstallServer(name)}>
      <label>{serverName}</label>
      <input
        style={{ marginLeft: "5%", marginTop: "1%" }}
        type="text"
        name="name"
        value={name}
        onChange={(e) => setName(e.target.value)}
      />
      <br />
      <label>Version</label>
      <input
        style={{ marginLeft: "5%", marginTop: "1%" }}
        type="text"
        name="version"
        value={version}
        onChange={(e) => setVersion(e.target.value)}
      />
      <br />
      <label>Port</label>
      <input
        style={{ marginLeft: "5%", marginTop: "1%" }}
        type="number"
        name="port"
        value={port}
        onChange={(e) => setPort(parseInt(e.target.value))}
      />
      <button type="submit">Submit</button>
      {availableVersions}
    </form>
  );
}
