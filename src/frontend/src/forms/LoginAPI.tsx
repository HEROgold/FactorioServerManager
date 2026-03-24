import { useState, FormEvent } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import Panel from "../templates/Panel";
import { SubmitButton } from "./SubmitButton";
import { validateForm, email, required } from "../utils/validation";

export function LoginFormAPI() {
  const [formData, setFormData] = useState({
    email: "",
    password: "",
  });
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [serverError, setServerError] = useState<string>("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const { login } = useAuth();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const next = searchParams.get("next") || "/servers";

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setServerError("");

    // Client-side validation
    const validationErrors = validateForm(formData, {
      email: [required("Email is required"), email()],
      password: [required("Password is required")],
    });

    if (Object.keys(validationErrors).length > 0) {
      setErrors(validationErrors);
      return;
    }

    setErrors({});
    setIsSubmitting(true);

    try {
      await login(formData.email, formData.password);
      navigate(next);
    } catch (error: any) {
      setServerError(error.message || "Login failed");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <Panel type="inset-lighter">
        <dl>
          <div>
            <dt>
              <label htmlFor="email">Email</label>
            </dt>
            <dd style={{ width: "90%" }}>
              <input
                id="email"
                name="email"
                type="email"
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                required
              />
              {errors.email && <p style={{ color: "red", fontSize: "0.875rem" }}>{errors.email}</p>}
            </dd>
          </div>

          <div>
            <dt>
              <label htmlFor="password">Password</label>
            </dt>
            <dd style={{ width: "90%" }}>
              <input
                id="password"
                name="password"
                type="password"
                value={formData.password}
                onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                required
              />
              {errors.password && <p style={{ color: "red", fontSize: "0.875rem" }}>{errors.password}</p>}
            </dd>
          </div>
        </dl>
      </Panel>

      {serverError && <p style={{ color: "red" }}>{serverError}</p>}

      <SubmitButton disabled={isSubmitting} />
    </form>
  );
}
