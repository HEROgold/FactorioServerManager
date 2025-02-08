import React, { useState } from "react";
import { useNavigate } from "react-router";
import { ENDPOINTS } from "../../constants.ts";

export default function LoginForm() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [emailAuthCode, setEmailAuthCode] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  function validateForm(): boolean {
    if (!email) {
      setError("Email is required");
      return false;
    }
    if (!password) {
      setError("Password is required");
      return false;
    }
    setLoading(true);
    return true;
  }

  async function handleSubmit(event) {
    event.preventDefault();
    if (!validateForm()) {
      return;
    }
    setLoading(true);

    const params = new URLSearchParams();
    params.append("email", email);
    params.append("password", password);
    params.append("emailAuthCode", emailAuthCode);

    try {
      const response = await fetch(ENDPOINTS.Login, {
        method: "POST",
        headers: {
          "Content-Type": "application/x-www-form-urlencoded",
        },
        body: params,
      });
      setLoading(false);
      if (response.ok) {
        response.json().then((data) => {
          localStorage.setItem("token", data.access_token);
          navigate("/home");
        });
      } else {
        const errorData = await response.json();
        setError(errorData.detail || "Authentication failed");
      }
    } catch (error) {
      setLoading(false);
      setError(error.message);
    }
    setLoading(false);
  }

  return (
    <form method="POST" action="/login" onSubmit={handleSubmit}>
      <div className="panel-inset-lighter">
        <dl>
          <div>
            <dt>Email</dt>
            <dd style={{ width: "90%" }}>
              <input
                type="email"
                required
                placeholder="Email"
                value={email}
                onChange={(e: { target: { value: any } }) =>
                  setEmail(e.target.value)
                }
              />
            </dd>
          </div>
          <div>
            <dt>Password</dt>
            <dd style={{ width: "90%" }}>
              <input
                type="password"
                required
                placeholder="Password"
                value={password}
                onChange={(e: { target: { value: any } }) =>
                  setPassword(e.target.value)
                }
              />
            </dd>
          </div>
          <div>
            <dt>Email Auth Code</dt>
            <dd style={{ width: "200%" }}>
              <input
                type="text"
                placeholder="(Optional) Email code"
                value={emailAuthCode}
                onChange={(e: { target: { value: any } }) =>
                  setEmailAuthCode(e.target.value)
                }
              />
            </dd>
          </div>
        </dl>
      </div>
      <div className="text-right">
        <button type="submit" className="button-green-right" disabled={loading}>
          {loading ? "Logging in..." : "Log in"}
        </button>
        {error && <div className="panel alert-error">{error}</div>}
      </div>
    </form>
  );
}
