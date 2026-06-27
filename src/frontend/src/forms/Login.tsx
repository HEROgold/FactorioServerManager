import { useState, type HTMLInputTypeAttribute, type ReactElement } from "react";
import { useSearchParams } from "react-router-dom";
import { SubmitButton } from "./SubmitButton";
import Panel from "@/templates/Panel";
import Input from "@/components/tags/Input";
import { sendJSON } from "@/api";

export interface LoginData {
  email: string;
  password: string;
  email_auth_code?: string;
}

interface InputProps {
  type: HTMLInputTypeAttribute;
  id?: string;
  name?: string;
  placeholder?: string;
  required?: boolean;
}

function GenericInput(props: InputProps) {
  return (
    <Input
      id={props.id ?? props.type}
      name={props.name ?? props.type}
      type={props.type}
      placeholder={props.placeholder}
      required={props.required}
    />
  );
}

export function LoginForm(): ReactElement {
  const [searchParams] = useSearchParams();
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const next = searchParams.get("next") || "/servers";

  const handleSubmit = async (e: React.SubmitEvent<HTMLFormElement>) => {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    const form = e.currentTarget;
    const value = (n: string) => (form.elements.namedItem(n) as HTMLInputElement | null)?.value ?? "";
    try {
      await sendJSON("/api/login", "POST", {
        email: value("email"),
        password: value("password"),
        email_auth_code: value("email_auth_code") || null,
      });
      // Force a full reload so the UserContext re-fetches /api/me with the cookie.
      window.location.href = next;
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <Panel type="inset-lighter">
        <dl>
          <div>
            <dt><label htmlFor="email">Email</label></dt>
            <dd style={{ width: "90%" }}>
              <GenericInput type="email" required={true} />
            </dd>
          </div>

          <div>
            <dt><label htmlFor="password">Password</label></dt>
            <dd style={{ width: "90%" }}>
              <GenericInput type="password" required={true} />
            </dd>
          </div>

          <div>
            <dt><label htmlFor="email_auth_code">Email Auth Code</label></dt>
            <dd style={{ width: "200%" }}>
              <GenericInput
                type="text"
                id="email_auth_code"
                name="email_auth_code"
                placeholder="Email Auth Code"
                required={false}
              />
            </dd>
          </div>
        </dl>
      </Panel>

      {error && <p style={{ color: "red" }}>{error}</p>}

      <SubmitButton idle="Log in" busy="Logging in..." submitting={submitting} />
    </form>
  );
}
