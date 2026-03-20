import type { HTMLInputTypeAttribute, ReactElement } from "react";
import {
  Form,
  useSearchParams,
  useActionData,
  useNavigation,
} from "react-router-dom";
import CSRF from "./CSRF";
import { SubmitButton } from "./SubmitButton";
import Panel from "@/templates/Panel";
import type { Children } from "@/interfaces/children";

export interface LoginData {
  email: string;
  password: string;
  email_auth_code?: string;
  next?: string;
}

interface InputProps {
  type: HTMLInputTypeAttribute;
  placeholder?: string;
  required?: boolean;
}

function GenericInput(props: InputProps) {
  return (
    <input
      id={props.type}
      name={props.type}
      type={props.type}
      placeholder={props.placeholder}
      required={props.required}
    />
  );
}

function EmailAuthCodeInput() {
  return (
    <GenericInput
      type="text"
      placeholder="Email Auth Code"
      required={false}
    />
  );
}

function PasswordInput() {
  return <GenericInput type="password" required={true} />;
}

function EmailInput() {
  return <GenericInput type="email" required={true} />;
}

function DescriptionList({children}: Children) {
  return <dl>{children}</dl>
}

export function LoginForm() {
  const [searchParams] = useSearchParams();
  const actionData = useActionData() as { error?: string } | undefined;
  const navigation = useNavigation();

  const next = searchParams.get("next") || "";

  return (
    <Form method="post">
      <CSRF />
      <input type="hidden" name="next" value={next} />

      <Panel type="inset-lighter">
        <dl>
          <div>
            <dt>
              <label htmlFor="email">Email</label>
            </dt>
            <dd style={{ width: "90%" }}>
              <EmailInput />
            </dd>
          </div>

          <div>
            <dt>
              <label htmlFor="password">Password</label>
            </dt>
            <dd style={{ width: "90%" }}>
              <PasswordInput />
            </dd>
          </div>

          <div>
            <dt>
              <label htmlFor="email_auth_code">Email Auth Code</label>
            </dt>
            <dd style={{ width: "200%" }}>
              <EmailAuthCodeInput />
            </dd>
          </div>
        </dl>
      </Panel>

      {actionData?.error && <p style={{ color: "red" }}>{actionData.error}</p>}

      <SubmitButton isSubmitting={navigation.state === "submitting"} />
    </Form>
  );
}
